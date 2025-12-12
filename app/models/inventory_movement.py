# app/models/inventory_movement.py
from sqlalchemy import Column, Integer, Float, ForeignKey, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    warehouse_src_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True) # nullable for IN
    warehouse_dest_id = Column(Integer, ForeignKey("warehouses.id"), nullable=True) # nullable for OUT
    qty = Column(Float, nullable=False)
    movement_type = Column(String, nullable=False) # IN / OUT / TRANSFER / ADJ
    reference = Column(String, nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("Item", lazy="joined")
    warehouse_src = relationship("Warehouse", foreign_keys=[warehouse_src_id], lazy="joined")
    warehouse_dest = relationship("Warehouse", foreign_keys=[warehouse_dest_id], lazy="joined")
