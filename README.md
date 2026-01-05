# ERP System API

A simple ERP system backend built with **FastAPI** and **SQLite**, featuring **user authentication**, **inventory management**, **warehouses**, **stock tracking**, and **audit-friendly inventory movements**.

---

## Table of Contents
1. [Features](#features)  
2. [Tech Stack](#tech-stack)  
3. [Project Structure](#project-structure)  
4. [Setup & Installation](#setup--installation)  
5. [API Endpoints](#api-endpoints)  
6. [Usage Examples](#usage-examples)  
7. [Notes & Design](#notes--design)  
8. [Future Improvements](#future-improvements)  

---

## Features

- **User Authentication**
  - Sign-up and login
  - Password hashing using bcrypt
  - JWT-based access tokens

- **Inventory Management**
  - Add, list, and retrieve items
  - Create and list warehouses
  - Track stock per warehouse
  - Perform inventory movements (IN, OUT, TRANSFER, ADJ)

- **Audit-Friendly**
  - Every inventory movement is recorded in `InventoryMovement` table
  - Atomic updates ensure stock consistency

---

## Tech Stack

- **Backend Framework:** FastAPI  
- **Database:** SQLite (via SQLAlchemy ORM)  
- **Authentication:** JWT + Passlib for password hashing  
- **Python Version:** 3.9+  

---

## Project Structure

app/
├── main.py # FastAPI app initialization
├── database.py # SQLAlchemy DB connection & session
├── auth.py # Password hashing and JWT functions
├── models/ # SQLAlchemy models
│ ├── user.py
│ ├── item.py
│ ├── warehouse.py
│ ├── stock.py
│ └── inventory_movement.py
├── routers/ # FastAPI API routers
│ ├── auth_router.py
│ └── inventory_router.py
└── schemas/ # (Optional) Pydantic schemas for request/response



## Setup & Installation

1. **Clone the repository**

git clone https://github.com/ssaurabh5135/erp-backend.git
cd erp-system
Create a virtual environment


python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate.bat         # Windows
Install dependencies



pip install fastapi sqlalchemy uvicorn passlib[bcrypt] python-jose
Run the FastAPI server



uvicorn app.main:app --reload
Access API docs

Open your browser: http://127.0.0.1:8000/docs

API Endpoints
Authentication
Method	Endpoint	Description
POST	/auth/signup	Register new user
POST	/auth/login	Login and get JWT token

Items
Method	Endpoint	Description
POST	/inventory/items	Create new item
GET	/inventory/items	List items
GET	/inventory/items/{id}	Get single item

Warehouses
Method	Endpoint	Description
POST	/inventory/warehouses	Create warehouse
GET	/inventory/warehouses	List warehouses

Stock
Method	Endpoint	Description
GET	/inventory/stock	List all stock
GET	/inventory/stock/item/{id}	Stock for a specific item

Inventory Movements
Method	Endpoint	Description
POST	/inventory/move	Perform IN, OUT, TRANSFER, ADJ movement

Usage Examples
Signup
POST /auth/signup
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepass123"
}

Login
POST /auth/login
{
  "email": "john@example.com",
  "password": "securepass123"
}

Response:
{
  "access_token": "jwt-token-here",
  "token_type": "bearer",
  "role": "viewer"
}

Create Item
POST /inventory/items
{
  "sku": "ITEM001",
  "name": "Laptop",
  "uom": "pcs",
  "description": "Gaming Laptop"
}

Create Warehouse
POST /inventory/warehouses
{
  "code": "WH001",
  "name": "Main Warehouse",
  "location": "New York"
}

Inventory Movement (IN)
POST /inventory/move
{
  "item_id": 1,
  "qty": 50,
  "movement_type": "IN",
  "warehouse_dest_id": 1,
  "current_user_id": 1
}

Notes & Design
Atomic operations: Stock update and movement log happen in one transaction.
Relationships allow easy queries:

stock.item.name
stock.warehouse.code
Secure passwords: Truncated & hashed before storing
JWT tokens for authenticated API access
Extensible: Add roles, more movement types, or reporting features

Future Improvements
Add role-based access control
Add reports for stock & movements
Use PostgreSQL/MySQL for production instead of SQLite
Add Pydantic schemas for better request validation
