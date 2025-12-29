from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import SessionLocal, engine, Base
from app.models.item import Item
from app.models.warehouse import Warehouse
from app.models.stock import Stock
from app.models.inventory_movement import InventoryMovement
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/inventory", tags=["Inventory"])

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Items ----------
@router.post("/items", status_code=201)
def create_item(sku: str, name: str, uom: str = "pcs", description: Optional[str] = None, db: Session = Depends(get_db)):
    item = Item(sku=sku, name=name, uom=uom, description=description)
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    return {"id": item.id, "sku": item.sku, "name": item.name, "uom": item.uom, "description": item.description}

@router.get("/items")
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(Item).offset(skip).limit(limit).all()
    return [{"id": i.id, "sku": i.sku, "name": i.name, "uom": i.uom, "description": i.description} for i in items]

@router.get("/items/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item.id, "sku": item.sku, "name": item.name, "uom": item.uom, "description": item.description}

# ---------- Warehouses ----------
@router.post("/warehouses", status_code=201)
def create_warehouse(code: str, name: str, location: Optional[str] = None, description: Optional[str] = None, db: Session = Depends(get_db)):
    wh = Warehouse(code=code, name=name, location=location, description=description)
    try:
        db.add(wh)
        db.commit()
        db.refresh(wh)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Warehouse code already exists")
    return {"id": wh.id, "code": wh.code, "name": wh.name, "location": wh.location, "description": wh.description}

@router.get("/warehouses")
def list_warehouses(db: Session = Depends(get_db)):
    whs = db.query(Warehouse).all()
    return [{"id": w.id, "code": w.code, "name": w.name, "location": w.location, "description": w.description} for w in whs]

# ---------- Stock ----------
@router.get("/stock")
def list_stock(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    stocks = db.query(Stock).offset(skip).limit(limit).all()
    return [
        {
            "id": s.id,
            "item_id": s.item_id,
            "warehouse_id": s.warehouse_id,
            "quantity": s.quantity,
            "item": {"id": s.item.id, "sku": s.item.sku, "name": s.item.name, "uom": s.item.uom, "description": s.item.description},
            "warehouse": {"id": s.warehouse.id, "code": s.warehouse.code, "name": s.warehouse.name, "location": s.warehouse.location, "description": s.warehouse.description}
        } for s in stocks
    ]

@router.get("/stock/item/{item_id}")
def stock_for_item(item_id: int, db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.item_id == item_id).all()
    return [
        {
            "id": s.id,
            "item_id": s.item_id,
            "warehouse_id": s.warehouse_id,
            "quantity": s.quantity,
            "item": {"id": s.item.id, "sku": s.item.sku, "name": s.item.name, "uom": s.item.uom, "description": s.item.description},
            "warehouse": {"id": s.warehouse.id, "code": s.warehouse.code, "name": s.warehouse.name, "location": s.warehouse.location, "description": s.warehouse.description}
        } for s in stocks
    ]

# ---------- Inventory Movements ----------
@router.post("/move", status_code=201)
def create_movement(
    item_id: int,
    qty: float,
    movement_type: str,
    current_user_id: int,
    warehouse_src_id: Optional[int] = None,
    warehouse_dest_id: Optional[int] = None,
    reference: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if movement_type not in ("IN", "OUT", "TRANSFER", "ADJ"):
        raise HTTPException(status_code=400, detail="Invalid movement_type")

    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # logic for IN, OUT, TRANSFER, ADJ
    movement = InventoryMovement(
        item_id=item_id,
        warehouse_src_id=warehouse_src_id,
        warehouse_dest_id=warehouse_dest_id,
        qty=qty,
        movement_type=movement_type,
        reference=reference,
        created_by=current_user_id
    )

    if movement_type == "IN":
        if not warehouse_dest_id:
            raise HTTPException(status_code=400, detail="warehouse_dest_id required for IN")
        stock = db.query(Stock).filter_by(item_id=item_id, warehouse_id=warehouse_dest_id).first()
        if not stock:
            stock = Stock(item_id=item_id, warehouse_id=warehouse_dest_id, quantity=0)
            db.add(stock)
            db.flush()
        stock.quantity += qty

    elif movement_type == "OUT":
        if not warehouse_src_id:
            raise HTTPException(status_code=400, detail="warehouse_src_id required for OUT")
        stock = db.query(Stock).filter_by(item_id=item_id, warehouse_id=warehouse_src_id).first()
        if not stock or stock.quantity < qty:
            raise HTTPException(status_code=400, detail="Insufficient stock for OUT")
        stock.quantity -= qty

    elif movement_type == "TRANSFER":
        if not warehouse_src_id or not warehouse_dest_id:
            raise HTTPException(status_code=400, detail="Both warehouse_src_id and warehouse_dest_id required for TRANSFER")
        stock_src = db.query(Stock).filter_by(item_id=item_id, warehouse_id=warehouse_src_id).first()
        if not stock_src or stock_src.quantity < qty:
            raise HTTPException(status_code=400, detail="Insufficient stock in source warehouse")
        stock_src.quantity -= qty
        stock_dest = db.query(Stock).filter_by(item_id=item_id, warehouse_id=warehouse_dest_id).first()
        if not stock_dest:
            stock_dest = Stock(item_id=item_id, warehouse_id=warehouse_dest_id, quantity=0)
            db.add(stock_dest)
            db.flush()
        stock_dest.quantity += qty

    elif movement_type == "ADJ":
        if not warehouse_dest_id:
            raise HTTPException(status_code=400, detail="warehouse_dest_id required for ADJ")
        stock = db.query(Stock).filter_by(item_id=item_id, warehouse_id=warehouse_dest_id).first()
        if not stock:
            stock = Stock(item_id=item_id, warehouse_id=warehouse_dest_id, quantity=0)
            db.add(stock)
            db.flush()
        stock.quantity += qty

    db.add(movement)
    db.commit()
    db.refresh(movement)
    return {
        "id": movement.id,
        "item_id": movement.item_id,
        "warehouse_src_id": movement.warehouse_src_id,
        "warehouse_dest_id": movement.warehouse_dest_id,
        "qty": movement.qty,
        "movement_type": movement.movement_type,
        "reference": movement.reference,
        "created_by": movement.created_by
    }
