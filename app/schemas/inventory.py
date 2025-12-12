# app/schemas/inventory.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Item schemas
class ItemCreate(BaseModel):
    sku: str
    name: str
    uom: str = "pcs"
    description: Optional[str] = None

class ItemOut(BaseModel):
    id: int
    sku: str
    name: str
    uom: str
    description: Optional[str]

    class Config:
        orm_mode = True

# Warehouse schemas
class WarehouseCreate(BaseModel):
    code: str
    name: str
    location: Optional[str] = None
    description: Optional[str] = None

class WarehouseOut(BaseModel):
    id: int
    code: str
    name: str
    location: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True

# Stock schema
class StockOut(BaseModel):
    id: int
    item_id: int
    warehouse_id: int
    quantity: float
    item: ItemOut
    warehouse: WarehouseOut

    class Config:
        orm_mode = True

# Movement schemas
class MovementCreate(BaseModel):
    item_id: int
    warehouse_src_id: Optional[int] = None
    warehouse_dest_id: Optional[int] = None
    qty: float
    movement_type: str # IN / OUT / TRANSFER / ADJ
    reference: Optional[str] = None

class MovementOut(BaseModel):
    id: int
    item_id: int
    warehouse_src_id: Optional[int]
    warehouse_dest_id: Optional[int]
    qty: float
    movement_type: str
    reference: Optional[str]
    created_by: Optional[int]
    created_at: datetime
    item: ItemOut

    class Config:
        orm_mode = True
