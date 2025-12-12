# app/models/stock.py
from sqlalchemy import Column, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Stock(Base):
    __tablename__ = "stock"
    __table_args__ = (UniqueConstraint("item_id", "warehouse_id", name="uix_item_warehouse"),)

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Float, default=0.0)

    # convenience relationships
    item = relationship("Item", lazy="joined")
    warehouse = relationship("Warehouse", lazy="joined")

