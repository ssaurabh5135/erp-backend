# app/models/item.py
from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    uom = Column(String, nullable=False, default="pcs")
    description = Column(Text, nullable=True)
