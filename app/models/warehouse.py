# app/models/warehouse.py
from sqlalchemy import Column, Integer, String, Text
from app.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=True)
