from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal

from app.models.sale import Sale
from app.models.purchase import Purchase
from app.models.payment import Payment
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.production import Production


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# REPORTS
# =========================================================

@router.get("/")
def get_reports(
    db: Session = Depends(get_db)
):

    # =====================================================
    # 1. SALES
    # =====================================================

    total_sales = db.query(
        func.coalesce(
            func.sum(Sale.total_amount),
            0
        )
    ).filter(
        Sale.status != "Cancelled"
    ).scalar()

    total_cogs = db.query(
        func.coalesce(
            func.sum(Sale.cogs),
            0
        )
    ).filter(
        Sale.status != "Cancelled"
    ).scalar()

    gross_profit = (
        float(total_sales or 0)
        - float(total_cogs or 0)
    )


    # =====================================================
    # 2. PURCHASES
    # =====================================================

    total_purchases = db.query(
        func.coalesce(
            func.sum(Purchase.total_amount),
            0
        )
    ).filter(
        Purchase.status != "Cancelled"
    ).scalar()


    # =====================================================
    # 3. CUSTOMER PAYMENTS
    # =====================================================

    total_received = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0
        )
    ).filter(
        Payment.party_type == "Customer",
        Payment.payment_status == "Paid"
    ).scalar()


    # =====================================================
    # 4. SUPPLIER PAYMENTS
    # =====================================================

    total_supplier_paid = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0
        )
    ).filter(
        Payment.party_type == "Supplier",
        Payment.payment_status == "Paid"
    ).scalar()


    # =====================================================
    # 5. EXPENSES
    # =====================================================

    total_expenses = db.query(
        func.coalesce(
            func.sum(Expense.amount),
            0
        )
    ).scalar()


    # =====================================================
    # 6. RECEIVABLES
    # =====================================================

    receivables = (
        float(total_sales or 0)
        - float(total_received or 0)
    )

    if receivables < 0:
        receivables = 0


    # =====================================================
    # 7. PAYABLES
    # =====================================================

    payables = (
        float(total_purchases or 0)
        - float(total_supplier_paid or 0)
    )

    if payables < 0:
        payables = 0


    # =====================================================
    # 8. NET PROFIT
    # =====================================================

    net_profit = (
        gross_profit
        - float(total_expenses or 0)
    )


    # =====================================================
    # 9. SALES COUNT
    # =====================================================

    sales_count = db.query(
        func.count(Sale.id)
    ).filter(
        Sale.status != "Cancelled"
    ).scalar()


    # =====================================================
    # 10. PURCHASE COUNT
    # =====================================================

    purchases_count = db.query(
        func.count(Purchase.id)
    ).filter(
        Purchase.status != "Cancelled"
    ).scalar()


    # =====================================================
    # 11. EXPENSE COUNT
    # =====================================================

    expenses_count = db.query(
        func.count(Expense.id)
    ).scalar()


    # =====================================================
    # 12. RAW MATERIAL STOCK
    # =====================================================

    raw_material_stock = db.query(
        func.coalesce(
            func.sum(Inventory.quantity),
            0
        )
    ).scalar()


    # =====================================================
    # 13. FINISHED PRODUCT STOCK
    # =====================================================

    finished_product_stock = db.query(
        func.coalesce(
            func.sum(Product.stock_quantity),
            0
        )
    ).scalar()


    # =====================================================
    # 14. PRODUCTION
    # =====================================================

    total_production = db.query(
        func.coalesce(
            func.sum(Production.output_quantity),
            0
        )
    ).filter(
        Production.status == "Completed"
    ).scalar()


    # =====================================================
    # 15. PROFIT MARGIN
    # =====================================================

    if float(total_sales or 0) > 0:
        profit_margin = (
            gross_profit
            / float(total_sales)
        ) * 100
    else:
        profit_margin = 0


    # =====================================================
    # 16. RETURN REPORT
    # =====================================================

    return {

        "financial_summary": {

            "total_sales": round(
                float(total_sales or 0),
                2
            ),

            "total_purchases": round(
                float(total_purchases or 0),
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

            "total_expenses": round(
                float(total_expenses or 0),
                2
            ),

            "net_profit": round(
                net_profit,
                2
            ),

            "profit_margin": round(
                profit_margin,
                2
            )
        },


        "cash_flow": {

            "customer_payments": round(
                float(total_received or 0),
                2
            ),

            "supplier_payments": round(
                float(total_supplier_paid or 0),
                2
            )
        },


        "outstanding": {

            "receivables": round(
                receivables,
                2
            ),

            "payables": round(
                payables,
                2
            )
        },


        "operations": {

            "sales_count": int(
                sales_count or 0
            ),

            "purchases_count": int(
                purchases_count or 0
            ),

            "expenses_count": int(
                expenses_count or 0
            ),

            "total_production": int(
                total_production or 0
            ),

            "raw_material_stock": int(
                raw_material_stock or 0
            ),

            "finished_product_stock": int(
                finished_product_stock or 0
            )
        }
    }