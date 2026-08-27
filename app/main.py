from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.database import engine, Base

# =========================================================
# MODELS
# =========================================================

from app.models.payment import Payment
from app.models.inventory import Inventory
from app.models.production import Production
from app.models.product import Product


# =========================================================
# AUTH / USERS / ADMIN
# =========================================================

from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.admin import router as admin_router

# =========================================================
# ROUTERS
# =========================================================

from app.routers.materials import router as materials_router
from app.routers.suppliers import router as suppliers_router
from app.routers.buyers import router as buyers_router
from app.routers.sales import router as sales_router
from app.routers.purchases import router as purchases_router
from app.routers.inventory import router as inventory_router
from app.routers.production import router as production_router
from app.routers.product import router as product_router
from app.routers.payments import router as payments_router
from app.routers.receivables import router as receivables_router
from app.routers.payables import router as payables_router
from app.routers.expenses import router as expenses_router
from app.routers.dashboard import router as dashboard_router
from app.routers.ai import router as ai_router
from app.routers.voice import router as voice_router
from app.routers.reports import router as reports_router


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="AI Rice Factory Automation",
    version="0.1.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# REGISTER ROUTERS
# =========================================================

app.include_router(materials_router)
app.include_router(suppliers_router)
app.include_router(buyers_router)
app.include_router(sales_router)
app.include_router(purchases_router)
app.include_router(inventory_router)
app.include_router(production_router)
app.include_router(product_router)
app.include_router(payments_router)
app.include_router(receivables_router)
app.include_router(payables_router)
app.include_router(expenses_router)
app.include_router(dashboard_router)
app.include_router(ai_router)
app.include_router(voice_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(reports_router)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Rice Factory Automation API is running"
    }


# =========================================================
# DATABASE TEST
# =========================================================

@app.get("/db-test")
def db_test():

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("SELECT 1")
            )

            return {
                "database": "Connected",
                "result": result.scalar()
            }

    except Exception as e:

        return {
            "database": "Connection failed",
            "error": str(e)
        }