from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.purchase import Purchase
from app.models.sale import Sale
from app.models.payment import Payment
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.production import Production


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db)
):

    # =========================================================
    # 1. TOTAL PURCHASES
    # Only non-cancelled purchases are counted
    # =========================================================

    total_purchases = db.query(
        func.coalesce(
            func.sum(Purchase.total_amount),
            0
        )
    ).filter(
        Purchase.status != "Cancelled"
    ).scalar()


    # =========================================================
    # 2. TOTAL SALES
    # Only non-cancelled sales are counted
    # =========================================================

    total_sales = db.query(
        func.coalesce(
            func.sum(Sale.total_amount),
            0
        )
    ).filter(
        Sale.status != "Cancelled"
    ).scalar()


    # =========================================================
    # 3. TOTAL COGS
    # =========================================================

    total_cogs = db.query(
        func.coalesce(
            func.sum(Sale.cogs),
            0
        )
    ).filter(
        Sale.status != "Cancelled"
    ).scalar()


    # =========================================================
    # 4. GROSS PROFIT
    # =========================================================

    gross_profit = (
        float(total_sales or 0)
        - float(total_cogs or 0)
    )


    # =========================================================
    # 5. CUSTOMER PAYMENTS RECEIVED
    # Only Paid customer payments
    # =========================================================

    total_received = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0
        )
    ).filter(
        Payment.party_type == "Customer",
        Payment.payment_status == "Paid"
    ).scalar()


    # =========================================================
    # 6. SUPPLIER PAYMENTS
    # Only Paid supplier payments
    # =========================================================

    total_supplier_paid = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0
        )
    ).filter(
        Payment.party_type == "Supplier",
        Payment.payment_status == "Paid"
    ).scalar()


    # =========================================================
    # 7. TOTAL EXPENSES
    # =========================================================

    total_expenses = db.query(
        func.coalesce(
            func.sum(Expense.amount),
            0
        )
    ).scalar()


    # =========================================================
    # 8. RECEIVABLES
    # =========================================================

    receivables = (
        float(total_sales or 0)
        - float(total_received or 0)
    )

    # Prevent negative receivables
    if receivables < 0:
        receivables = 0


    # =========================================================
    # 9. PAYABLES
    # =========================================================

    payables = (
        float(total_purchases or 0)
        - float(total_supplier_paid or 0)
    )

    # Prevent negative payables
    if payables < 0:
        payables = 0


    # =========================================================
    # 10. RAW MATERIAL STOCK
    # =========================================================

    raw_material_stock = db.query(
        func.coalesce(
            func.sum(Inventory.quantity),
            0
        )
    ).scalar()


    # =========================================================
    # 11. FINISHED PRODUCT STOCK
    # =========================================================

    finished_product_stock = db.query(
        func.coalesce(
            func.sum(Product.stock_quantity),
            0
        )
    ).scalar()


    # =========================================================
    # 12. TOTAL COMPLETED PRODUCTION
    # =========================================================

    total_production = db.query(
        func.coalesce(
            func.sum(Production.output_quantity),
            0
        )
    ).filter(
        Production.status == "Completed"
    ).scalar()


    # =========================================================
    # 13. NET PROFIT
    # =========================================================

    net_profit = (
        gross_profit
        - float(total_expenses or 0)
    )


    # =========================================================
    # 14. RESPONSE
    # =========================================================

    return {
        "total_purchases": round(
            float(total_purchases or 0),
            2
        ),

        "total_sales": round(
            float(total_sales or 0),
            2
        ),

        "total_cogs": round(
            float(total_cogs or 0),
            2
        ),

        "gross_profit": round(
            gross_profit,
            2
        ),

        "total_received": round(
            float(total_received or 0),
            2
        ),

        "total_supplier_paid": round(
            float(total_supplier_paid or 0),
            2
        ),

        "total_expenses": round(
            float(total_expenses or 0),
            2
        ),

        "total_receivables": round(
            receivables,
            2
        ),

        "total_payables": round(
            payables,
            2
        ),

        "raw_material_stock": int(
            raw_material_stock or 0
        ),

        "finished_product_stock": int(
            finished_product_stock or 0
        ),

        "total_production": int(
            total_production or 0
        ),

        "net_profit": round(
            net_profit,
            2
        )
    }
