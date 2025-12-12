# app/routers/inventory_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import SessionLocal, engine, Base
from app.schemas.inventory import (
    ItemCreate, ItemOut,
    WarehouseCreate, WarehouseOut,
    StockOut,
    MovementCreate, MovementOut
)
from app.models.item import Item
from app.models.warehouse import Warehouse
from app.models.stock import Stock
from app.models.inventory_movement import InventoryMovement
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# create tables for the new models if not created
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Items ----------
@router.post("/items", response_model=ItemOut, status_code=201)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(sku=payload.sku, name=payload.name, uom=payload.uom, description=payload.description)
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    return item

@router.get("/items", response_model=List[ItemOut])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()

@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

# ---------- Warehouses ----------
@router.post("/warehouses", response_model=WarehouseOut, status_code=201)
def create_warehouse(payload: WarehouseCreate, db: Session = Depends(get_db)):
    wh = Warehouse(code=payload.code, name=payload.name, location=payload.location, description=payload.description)
    try:
        db.add(wh)
        db.commit()
        db.refresh(wh)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Warehouse code already exists")
    return wh

@router.get("/warehouses", response_model=List[WarehouseOut])
def list_warehouses(db: Session = Depends(get_db)):
    return db.query(Warehouse).all()

# ---------- Stock ----------
@router.get("/stock", response_model=List[StockOut])
def list_stock(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    return db.query(Stock).offset(skip).limit(limit).all()

@router.get("/stock/item/{item_id}", response_model=List[StockOut])
def stock_for_item(item_id: int, db: Session = Depends(get_db)):
    return db.query(Stock).filter(Stock.item_id == item_id).all()

# ---------- Inventory Movements (atomic) ----------
@router.post("/move", response_model=MovementOut, status_code=201)
def create_movement(payload: MovementCreate, db: Session = Depends(get_db), current_user_id: int = None):
    if payload.movement_type not in ("IN", "OUT", "TRANSFER", "ADJ"):
        raise HTTPException(status_code=400, detail="Invalid movement_type")

    try:
        # check item exists
        item = db.get(Item, payload.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # IN: increase destination warehouse
        if payload.movement_type == "IN":
            if payload.warehouse_dest_id is None:
                raise HTTPException(status_code=400, detail="warehouse_dest_id required for IN")
            stock = db.query(Stock).filter_by(item_id=payload.item_id, warehouse_id=payload.warehouse_dest_id).first()
            if not stock:
                stock = Stock(item_id=payload.item_id, warehouse_id=payload.warehouse_dest_id, quantity=0.0)
                db.add(stock)
                db.flush()
            stock.quantity = stock.quantity + payload.qty

            movement = InventoryMovement(
                item_id=payload.item_id,
                warehouse_src_id=None,
                warehouse_dest_id=payload.warehouse_dest_id,
                qty=payload.qty,
                movement_type=payload.movement_type,
                reference=payload.reference,
                created_by=current_user_id
            )
            db.add(movement)

        # OUT: decrease source warehouse
        elif payload.movement_type == "OUT":
            if payload.warehouse_src_id is None:
                raise HTTPException(status_code=400, detail="warehouse_src_id required for OUT")
            stock = db.query(Stock).filter_by(item_id=payload.item_id, warehouse_id=payload.warehouse_src_id).first()
            if not stock or stock.quantity < payload.qty:
                raise HTTPException(status_code=400, detail="Insufficient stock for OUT")
            stock.quantity = stock.quantity - payload.qty

            movement = InventoryMovement(
                item_id=payload.item_id,
                warehouse_src_id=payload.warehouse_src_id,
                warehouse_dest_id=None,
                qty=payload.qty,
                movement_type=payload.movement_type,
                reference=payload.reference,
                created_by=current_user_id
            )
            db.add(movement)

        # TRANSFER: move between warehouses
        elif payload.movement_type == "TRANSFER":
            if payload.warehouse_src_id is None or payload.warehouse_dest_id is None:
                raise HTTPException(status_code=400, detail="warehouse_src_id and warehouse_dest_id required for TRANSFER")
            if payload.warehouse_src_id == payload.warehouse_dest_id:
                raise HTTPException(status_code=400, detail="Source and destination warehouses must differ")

            stock_src = db.query(Stock).filter_by(item_id=payload.item_id, warehouse_id=payload.warehouse_src_id).first()
            if not stock_src or stock_src.quantity < payload.qty:
                raise HTTPException(status_code=400, detail="Insufficient stock in source warehouse")
            stock_src.quantity = stock_src.quantity - payload.qty

            stock_dest = db.query(Stock).filter_by(item_id=payload.item_id, warehouse_id=payload.warehouse_dest_id).first()
            if not stock_dest:
                stock_dest = Stock(item_id=payload.item_id, warehouse_id=payload.warehouse_dest_id, quantity=0.0)
                db.add(stock_dest)
                db.flush()
            stock_dest.quantity = stock_dest.quantity + payload.qty

            movement = InventoryMovement(
                item_id=payload.item_id,
                warehouse_src_id=payload.warehouse_src_id,
                warehouse_dest_id=payload.warehouse_dest_id,
                qty=payload.qty,
                movement_type=payload.movement_type,
                reference=payload.reference,
                created_by=current_user_id
            )
            db.add(movement)

        # ADJ: adjustment (can be positive or negative)
        elif payload.movement_type == "ADJ":
            if payload.warehouse_dest_id is None:
                raise HTTPException(status_code=400, detail="warehouse_dest_id required for ADJ")
            stock = db.query(Stock).filter_by(item_id=payload.item_id, warehouse_id=payload.warehouse_dest_id).first()
            if not stock:
                stock = Stock(item_id=payload.item_id, warehouse_id=payload.warehouse_dest_id, quantity=0.0)
                db.add(stock)
                db.flush()
            stock.quantity = stock.quantity + payload.qty

            movement = InventoryMovement(
                item_id=payload.item_id,
                warehouse_src_id=None,
                warehouse_dest_id=payload.warehouse_dest_id,
                qty=payload.qty,
                movement_type=payload.movement_type,
                reference=payload.reference,
                created_by=current_user_id
            )
            db.add(movement)

        db.commit()
        db.refresh(movement)
        return movement

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create movement: {exc}")
