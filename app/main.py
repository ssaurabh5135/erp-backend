# app/main.py
from fastapi import FastAPI
from app.database import Base, engine
# import routers so they register
from app.routers import auth_router, inventory_router
# import models so tables are created by metadata.create_all
from app.models import user, item, warehouse, stock, inventory_movement

# create all tables (safe to call multiple times)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ERP System API")

app.include_router(auth_router.router)
app.include_router(inventory_router.router)

