from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from google import genai
from app.models.supplier import Supplier
from app.models.material import Material
from typing import Dict
from dotenv import load_dotenv
from sqlalchemy import func
from datetime import date, timedelta
import os
import json

from app.database import SessionLocal

from app.models.sale import Sale
from app.models.purchase import Purchase
from app.models.payment import Payment
from app.models.expense import Expense
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.production import Production

from app.ai_actions import (
    create_purchase_action,
    create_sale_action
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"]
)


# ============================================================
# GEMINI CLIENT
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not configured in the .env file."
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# DATABASE
# ============================================================

def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ============================================================
# PURCHASE MEMORY
# ============================================================

purchase_memory: Dict[str, dict] = {}


# ============================================================
# SALE MEMORY
# ============================================================

sale_memory: Dict[str, dict] = {}


# ============================================================
# AI CHAT REQUEST
# ============================================================

class AIRequest(BaseModel):
    message: str


# ============================================================
# PURCHASE REQUEST
# ============================================================

class PurchaseAIRequest(BaseModel):
    session_id: str
    message: str


# ============================================================
# SALE REQUEST
# ============================================================

class SaleAIRequest(BaseModel):
    session_id: str
    message: str


# ============================================================
# CLEAN GEMINI JSON
# ============================================================

def clean_json_response(text: str) -> str:
    """
    Gemini کبھی JSON کو markdown code fence میں واپس کرتا ہے۔
    یہ function code fences اور اضافی whitespace remove کرتا ہے۔
    """

    if not text:
        return ""

    text = text.strip()

    # Remove ```json
    if text.startswith("```json"):
        text = text[len("```json"):]

    # Remove ```JSON
    elif text.startswith("```JSON"):
        text = text[len("```JSON"):]

    # Remove ```
    elif text.startswith("```"):
        text = text[len("```"):]

    # Remove ending ```
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(value, default=None):
    """
    Safely convert a value to float.
    """

    if value is None:
        return default

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


# ============================================================
# SAFE INT
# ============================================================

def safe_int(value, default=None):
    """
    Safely convert a value to int.
    """

    if value is None:
        return default

    try:
        return int(float(value))

    except (TypeError, ValueError):
        return default


# ============================================================
# COMPLETE FACTORY DATA
# ============================================================

def get_factory_data(db: Session):

    # --------------------------------------------------------
    # TOTAL SALES
    # --------------------------------------------------------

    total_sales = db.query(
        func.coalesce(
            func.sum(Sale.total_amount),
            0
        )
    ).scalar()

    # --------------------------------------------------------
    # TOTAL COGS
    # --------------------------------------------------------

    total_cogs = db.query(
        func.coalesce(
            func.sum(Sale.cogs),
            0
        )
    ).scalar()

    # --------------------------------------------------------
    # CUSTOMER PAYMENTS
    # --------------------------------------------------------

    total_received = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0
        )
    ).filter(
        Payment.party_type == "Customer",
        Payment.payment_status == "Paid"
    ).scalar()

    # --------------------------------------------------------
    # TOTAL PURCHASES
    # --------------------------------------------------------

    total_purchases = db.query(
        func.coalesce(
            func.sum(Purchase.total_amount),
            0
        )
    ).scalar()

    # --------------------------------------------------------
    # SUPPLIER PAYMENTS
    # --------------------------------------------------------

    total_supplier_paid = db.query(
        func.coalesce(
            func.sum(Payment.amount),
            0
        )
    ).filter(
        Payment.party_type == "Supplier",
        Payment.payment_status == "Paid"
    ).scalar()

    # --------------------------------------------------------
    # EXPENSES
    # --------------------------------------------------------

    total_expenses = db.query(
        func.coalesce(
            func.sum(Expense.amount),
            0
        )
    ).scalar()

    # --------------------------------------------------------
    # RAW MATERIAL STOCK
    # --------------------------------------------------------

    raw_material_stock = db.query(
        func.coalesce(
            func.sum(Inventory.quantity),
            0
        )
    ).scalar()

    # --------------------------------------------------------
    # FINISHED PRODUCT STOCK
    # --------------------------------------------------------

    finished_product_stock = db.query(
        func.coalesce(
            func.sum(Product.stock_quantity),
            0
        )
    ).scalar()

    # --------------------------------------------------------
    # TOTAL PRODUCTION
    # --------------------------------------------------------

    total_production = db.query(
        func.coalesce(
            func.sum(Production.output_quantity),
            0
        )
    ).filter(
        Production.status == "Completed"
    ).scalar()

    # --------------------------------------------------------
    # CALCULATIONS
    # --------------------------------------------------------

    total_sales_value = float(total_sales or 0)
    total_cogs_value = float(total_cogs or 0)
    total_received_value = float(total_received or 0)
    total_purchases_value = float(total_purchases or 0)
    total_supplier_paid_value = float(
        total_supplier_paid or 0
    )
    total_expenses_value = float(total_expenses or 0)

    gross_profit = (
        total_sales_value
        - total_cogs_value
    )

    net_profit = (
        gross_profit
        - total_expenses_value
    )

    receivables = (
        total_sales_value
        - total_received_value
    )

    payables = (
        total_purchases_value
        - total_supplier_paid_value
    )

    return {

        "total_sales": total_sales_value,

        "total_cogs": total_cogs_value,

        "gross_profit": gross_profit,

        "total_received": total_received_value,

        "total_purchases": total_purchases_value,

        "total_supplier_paid": total_supplier_paid_value,

        "total_expenses": total_expenses_value,

        "receivables": receivables,

        "payables": payables,

        "raw_material_stock": int(
            raw_material_stock or 0
        ),

        "finished_product_stock": int(
            finished_product_stock or 0
        ),

        "total_production": int(
            total_production or 0
        ),

        "net_profit": net_profit
    }


# ============================================================
# TODAY SALES
# ============================================================

def get_today_sales(db: Session):

    today = date.today()

    tomorrow = today + timedelta(days=1)

    sales = db.query(Sale).filter(
        Sale.created_at >= today,
        Sale.created_at < tomorrow
    ).all()

    total_today_sales = sum(
        float(s.total_amount or 0)
        for s in sales
    )

    total_today_cogs = sum(
        float(s.cogs or 0)
        for s in sales
    )

    total_today_profit = (
        total_today_sales
        - total_today_cogs
    )

    return {

        "date": str(today),

        "number_of_sales": len(sales),

        "total_sales": total_today_sales,

        "total_cogs": total_today_cogs,

        "gross_profit": total_today_profit
    }


# ============================================================
# GENERATE AI CHAT REPLY
# ============================================================

def generate_ai_reply(
    message: str,
    db: Session
):

    factory_data = get_factory_data(db)

    today_sales = get_today_sales(db)

    prompt = f"""
You are the AI Business Assistant of a Rice Factory.

The owner can ask questions in:

- English
- Urdu
- Roman Urdu

Always answer in simple Urdu script.

IMPORTANT RULES:

1. Use ONLY the database data provided below.
2. Never invent numbers.
3. Never estimate numbers.
4. Never change database numbers.
5. Never mix today's data with lifetime/factory totals.
6. Return ONLY ONE final answer.
7. Do not return JSON.
8. Do not explain internal reasoning.
9. If information is unavailable, use the exact unavailable-information response.
10. Money should be shown with "روپے".
11. Avoid unnecessary decimal digits when the value is mathematically a whole number.
12. If a decimal is necessary, use a reasonable readable format.

============================================================
COMPLETE FACTORY DATA
============================================================

{json.dumps(factory_data, ensure_ascii=False, indent=2)}

============================================================
TODAY'S SALES DATA
============================================================

{json.dumps(today_sales, ensure_ascii=False, indent=2)}

============================================================
QUESTION RULES
============================================================

1. TODAY'S SALES

If the owner asks:

"آج کی sales"
"آج کی total sales"
"today sales"
"today's sales"
"aaj ki sale"
"aaj ki total sale"
"aaj ki total sales"

Use ONLY:

TODAY'S SALES DATA -> total_sales

Do NOT use COMPLETE FACTORY DATA.

------------------------------------------------------------

2. TOTAL FACTORY SALES

If the owner asks:

"کل sales"
"total sales"
"factory ki total sales"
"all sales"
"مکمل sales"

Use:

COMPLETE FACTORY DATA -> total_sales

------------------------------------------------------------

3. TODAY'S COGS

If the owner asks:

"آج کی COGS"
"today COGS"
"aaj ka COGS"

Use:

TODAY'S SALES DATA -> total_cogs

------------------------------------------------------------

4. TODAY'S PROFIT

If the owner asks:

"آج کا profit"
"today profit"
"aaj ka profit"
"آج کا منافع"

Use:

TODAY'S SALES DATA -> gross_profit

------------------------------------------------------------

5. TOTAL / NET PROFIT

If the owner asks:

"total profit"
"net profit"
"factory ka net profit"
"مکمل منافع"
"نیٹ پرافٹ"

Use:

COMPLETE FACTORY DATA -> net_profit

------------------------------------------------------------

6. TOTAL PURCHASES

If the owner asks:

"total purchases"
"کل purchases"
"factory ki purchases"
"مکمل purchases"

Use:

COMPLETE FACTORY DATA -> total_purchases

------------------------------------------------------------

7. TODAY'S PURCHASES

If the owner asks:

"today purchases"
"آج کی purchases"
"aaj ki purchase"

The database data currently does not provide today's purchase total.

Answer EXACTLY:

"یہ معلومات ابھی database میں دستیاب نہیں ہیں۔"

------------------------------------------------------------

8. RAW MATERIAL STOCK

If the owner asks about:

"raw material stock"
"را مٹیریل"
"raw material"
"خام مال"
"raw material ka stock"

Use:

COMPLETE FACTORY DATA -> raw_material_stock

------------------------------------------------------------

9. FINISHED PRODUCT STOCK

If the owner asks about:

"finished product stock"
"finished stock"
"تیار مال"
"finished product"

Use:

COMPLETE FACTORY DATA -> finished_product_stock

------------------------------------------------------------

10. PRODUCTION

If the owner asks about:

"production"
"total production"
"آج production" only if today's production data exists

Use:

COMPLETE FACTORY DATA -> total_production

If the owner specifically asks for today's production, remember that
the provided database data does NOT contain today's production total.

In that case answer EXACTLY:

"یہ معلومات ابھی database میں دستیاب نہیں ہیں۔"

------------------------------------------------------------

11. EXPENSES

If the owner asks about:

"expenses"
"total expenses"
"خرچے"
"کل خرچے"

Use:

COMPLETE FACTORY DATA -> total_expenses

------------------------------------------------------------

12. RECEIVABLES

If the owner asks about:

"receivables"
"customer se kitne lene hain"
"customers se kitne lene hain"
"کسٹمرز سے کتنے لینے ہیں"
"لینے والی رقم"

Use:

COMPLETE FACTORY DATA -> receivables

------------------------------------------------------------

13. PAYABLES

If the owner asks about:

"payables"
"supplier ko kitne dene hain"
"suppliers ko kitne dene hain"
"سپلائرز کو کتنے دینے ہیں"
"دینے والی رقم"

Use:

COMPLETE FACTORY DATA -> payables

------------------------------------------------------------

14. IF INFORMATION IS NOT AVAILABLE

Answer EXACTLY:

"یہ معلومات ابھی database میں دستیاب نہیں ہیں۔"

------------------------------------------------------------

15. UNCLEAR QUESTION

If the question is genuinely unclear, ask one short clarification
question in Urdu.

============================================================
TODAY
============================================================

{today_sales["date"]}

============================================================
OWNER QUESTION
============================================================

{message}

============================================================
FINAL INSTRUCTION
============================================================

Return ONLY the final answer to the owner.
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text.strip()


# ============================================================
# AI CHAT ENDPOINT
# ============================================================

@router.post("/chat")
def ai_chat(
    request: AIRequest,
    db: Session = Depends(get_db)
):

    reply = generate_ai_reply(
        message=request.message,
        db=db
    )

    return {
        "reply": reply
    }


# ============================================================
# CREATE PURCHASE ACTION
# ============================================================

def create_purchase_action(
    db: Session,
    supplier_name: str,
    material_name: str,
    quantity: int,
    purchase_rate: float | None,
    transport_cost: float = 0,
    notes: str | None = None
):

    # --------------------------------------------------------
    # FIND SUPPLIER
    # --------------------------------------------------------

    supplier = db.query(Supplier).filter(
        func.lower(Supplier.name) == supplier_name.strip().lower()
    ).first()

    if not supplier:
        return {
            "success": False,
            "message": f"Supplier '{supplier_name}' database میں موجود نہیں ہے۔"
        }

    # --------------------------------------------------------
    # FIND MATERIAL
    # --------------------------------------------------------

    material = db.query(Material).filter(
        func.lower(Material.name) == material_name.strip().lower()
    ).first()

    if not material:
        return {
            "success": False,
            "message": f"Material '{material_name}' database میں موجود نہیں ہے۔"
        }

    # --------------------------------------------------------
    # PURCHASE RATE
    # --------------------------------------------------------

    if purchase_rate is None:
        return {
            "success": False,
            "status": "waiting_for_purchase_rate",
            "message": "Purchase rate فراہم کریں۔"
        }

    purchase_rate = float(purchase_rate)
    transport_cost = float(transport_cost or 0)

    if purchase_rate < 0:
        return {
            "success": False,
            "message": "Purchase rate درست درج کریں۔"
        }

    if transport_cost < 0:
        return {
            "success": False,
            "message": "Transport cost درست درج کریں۔"
        }

    # --------------------------------------------------------
    # CALCULATE TOTAL
    # --------------------------------------------------------

    total_amount = (
        quantity * purchase_rate
    ) + transport_cost

    # --------------------------------------------------------
    # CREATE PURCHASE
    # --------------------------------------------------------

    purchase = Purchase(
        supplier_id=supplier.id,
        material_id=material.id,
        quantity=quantity,
        purchase_rate=purchase_rate,
        transport_cost=transport_cost,
        total_amount=total_amount,
        payment_status="Pending",
        status="Pending",
        availability_status="Available",
        notes=notes
    )

    db.add(purchase)
    db.commit()
    db.refresh(purchase)

    # --------------------------------------------------------
    # UPDATE INVENTORY
    # --------------------------------------------------------

    inventory = db.query(Inventory).filter(
        Inventory.material_id == material.id
    ).first()

    if inventory:

        old_quantity = float(
            inventory.quantity or 0
        )

        old_rate = float(
            inventory.average_rate or 0
        )

        new_quantity = old_quantity + quantity

        if new_quantity > 0:

            inventory.average_rate = (
                (
                    old_quantity * old_rate
                ) + (
                    quantity * purchase_rate
                )
            ) / new_quantity

        inventory.quantity = new_quantity

    else:

        inventory = Inventory(
            material_id=material.id,
            quantity=quantity,
            average_rate=purchase_rate
        )

        db.add(inventory)

    db.commit()
    db.refresh(inventory)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,
        "message": "AI purchase successfully created.",
        "purchase": {
            "id": purchase.id,
            "supplier_id": purchase.supplier_id,
            "material_id": purchase.material_id,
            "quantity": purchase.quantity,
            "purchase_rate": purchase.purchase_rate,
            "transport_cost": purchase.transport_cost,
            "total_amount": purchase.total_amount,
            "payment_status": purchase.payment_status,
            "status": purchase.status
        },
        "inventory": {
            "material_id": inventory.material_id,
            "quantity": inventory.quantity,
            "average_rate": inventory.average_rate
        }
    }



# ============================================================
# AI PURCHASE AUTOMATION
# ============================================================

@router.post("/purchase")
def ai_purchase(
    request: PurchaseAIRequest,
    db: Session = Depends(get_db)
):

    session_id = request.session_id
    message = request.message.strip()

    if not message:
        return {
            "success": False,
            "message": "Purchase کی معلومات فراہم کریں۔"
        }

    memory = purchase_memory.get(
        session_id,
        {}
    )

    prompt = f"""
You are a Rice Factory Purchase Assistant.

The owner may speak in:

- English
- Urdu
- Roman Urdu

Your job is to extract purchase information from the
CURRENT message while keeping valid information from the
PREVIOUS conversation.

============================================================
PREVIOUS PURCHASE INFORMATION
============================================================

{json.dumps(memory, ensure_ascii=False, indent=2)}

============================================================
CURRENT OWNER MESSAGE
============================================================

{message}

============================================================
FIELDS TO EXTRACT
============================================================

supplier_name
material_name
quantity
purchase_rate
transport_cost
notes

============================================================
STRICT RULES
============================================================

1. Return ONLY valid JSON.
2. Do not return markdown.
3. Do not use ```json.
4. Do not invent missing information.
5. Keep valid previous information.
6. If the owner corrects previous information, replace the old
   information with the new information.
7. If the owner says "نہیں" or corrects a supplier/material/etc.,
   use the corrected value.
8. Numbers must remain numbers.
9. If a field is missing, return null.
10. Do not create a purchase yourself.
11. Only extract information.

Example:

{{
    "supplier_name": "Al-Rehman Rice Supplier",
    "material_name": "Phak",
    "quantity": 1000,
    "purchase_rate": null,
    "transport_cost": null,
    "notes": null
}}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    try:

        clean_text = clean_json_response(
            response.text
        )

        data = json.loads(
            clean_text
        )

        if not isinstance(data, dict):
            raise ValueError(
                "AI response is not a JSON object."
            )

    except Exception:

        return {
            "success": False,
            "message": (
                "AI purchase information سمجھ نہیں سکا۔ "
                "براہ کرم دوبارہ واضح کریں۔"
            )
        }

    fields = [
        "supplier_name",
        "material_name",
        "quantity",
        "purchase_rate",
        "transport_cost",
        "notes"
    ]

    # --------------------------------------------------------
    # UPDATE MEMORY
    # --------------------------------------------------------

    for key in fields:

        value = data.get(key)

        if value is not None:

            if isinstance(value, str):

                value = value.strip()

                if not value:
                    continue

            memory[key] = value

    purchase_memory[session_id] = memory

    # --------------------------------------------------------
    # SUPPLIER CHECK
    # --------------------------------------------------------

    if not memory.get("supplier_name"):

        return {
            "success": False,
            "status": "waiting_for_supplier",
            "message": "کس supplier سے خریدنا ہے؟"
        }

    # --------------------------------------------------------
    # MATERIAL CHECK
    # --------------------------------------------------------

    if not memory.get("material_name"):

        return {
            "success": False,
            "status": "waiting_for_material",
            "message": "کون سا material خریدنا ہے؟"
        }

    # --------------------------------------------------------
    # QUANTITY CHECK
    # --------------------------------------------------------

    quantity = safe_int(
        memory.get("quantity")
    )

    if quantity is None or quantity <= 0:

        return {
            "success": False,
            "status": "waiting_for_quantity",
            "message": "کتنی مقدار خریدنی ہے؟"
        }

    # --------------------------------------------------------
    # PURCHASE RATE
    # --------------------------------------------------------

    purchase_rate = safe_float(
        memory.get("purchase_rate")
    )

    if purchase_rate is not None and purchase_rate < 0:

        return {
            "success": False,
            "status": "invalid_purchase_rate",
            "message": "Purchase rate درست درج کریں۔"
        }

    # --------------------------------------------------------
    # TRANSPORT COST
    # --------------------------------------------------------

    transport_cost = safe_float(
        memory.get("transport_cost")
    )

    if transport_cost is not None and transport_cost < 0:

        return {
            "success": False,
            "status": "invalid_transport_cost",
            "message": "Transport cost درست درج کریں۔"
        }

    # --------------------------------------------------------
    # CREATE PURCHASE
    # --------------------------------------------------------

    result = create_purchase_action(

        db=db,

        supplier_name=memory["supplier_name"],

        material_name=memory["material_name"],

        quantity=quantity,

        purchase_rate=purchase_rate,

        transport_cost=transport_cost,

        notes=memory.get("notes")
    )

    # --------------------------------------------------------
    # CLEAR MEMORY AFTER SUCCESS
    # --------------------------------------------------------

    if result.get("success"):

        purchase_memory.pop(
            session_id,
            None
        )

    return result


# ============================================================
# AI SALE AUTOMATION
# ============================================================

@router.post("/sale")
def ai_sale(
    request: SaleAIRequest,
    db: Session = Depends(get_db)
):

    session_id = request.session_id
    message = request.message.strip()

    if not message:
        return {
            "success": False,
            "message": "Sale کی معلومات فراہم کریں۔"
        }

    memory = sale_memory.get(
        session_id,
        {}
    )

    prompt = f"""
You are a Rice Factory Sales Assistant.

The owner may speak in:

- English
- Urdu
- Roman Urdu

Your job is to extract sales information from the
CURRENT message while keeping valid information from the
PREVIOUS conversation.

============================================================
PREVIOUS SALE INFORMATION
============================================================

{json.dumps(memory, ensure_ascii=False, indent=2)}

============================================================
CURRENT OWNER MESSAGE
============================================================

{message}

============================================================
FIELDS TO EXTRACT
============================================================

buyer_name
product_name
quantity
selling_rate
transport_cost
notes

============================================================
STRICT RULES
============================================================

1. Return ONLY valid JSON.
2. Do not return markdown.
3. Do not use ```json.
4. Do not invent missing information.
5. Keep valid previous information.
6. If the owner corrects previous information, replace the old
   information with the new information.
7. If the owner says "نہیں" or corrects a buyer/product/etc.,
   use the corrected value.
8. Numbers must remain numbers.
9. If a field is missing, return null.
10. Do not create a sale yourself.
11. Only extract information.

Example:

{{
    "buyer_name": "ABC Rice Mills",
    "product_name": "Phak Rice",
    "quantity": 10,
    "selling_rate": 300,
    "transport_cost": 500,
    "notes": null
}}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    try:

        clean_text = clean_json_response(
            response.text
        )

        data = json.loads(
            clean_text
        )

        if not isinstance(data, dict):
            raise ValueError(
                "AI response is not a JSON object."
            )

    except Exception:

        return {
            "success": False,
            "message": (
                "AI sale information سمجھ نہیں سکا۔ "
                "براہ کرم دوبارہ واضح کریں۔"
            )
        }

    fields = [
        "buyer_name",
        "product_name",
        "quantity",
        "selling_rate",
        "transport_cost",
        "notes"
    ]

    # --------------------------------------------------------
    # UPDATE MEMORY
    # --------------------------------------------------------

    for key in fields:

        value = data.get(key)

        if value is not None:

            if isinstance(value, str):

                value = value.strip()

                if not value:
                    continue

            memory[key] = value

    sale_memory[session_id] = memory

    # --------------------------------------------------------
    # BUYER CHECK
    # --------------------------------------------------------

    if not memory.get("buyer_name"):

        return {
            "success": False,
            "status": "waiting_for_buyer",
            "message": "کس buyer کو sale کرنی ہے؟"
        }

    # --------------------------------------------------------
    # PRODUCT CHECK
    # --------------------------------------------------------

    if not memory.get("product_name"):

        return {
            "success": False,
            "status": "waiting_for_product",
            "message": "کون سا product فروخت کرنا ہے؟"
        }

    # --------------------------------------------------------
    # QUANTITY CHECK
    # --------------------------------------------------------

    quantity = safe_int(
        memory.get("quantity")
    )

    if quantity is None or quantity <= 0:

        return {
            "success": False,
            "status": "waiting_for_quantity",
            "message": "کتنی مقدار فروخت کرنی ہے؟"
        }

    # --------------------------------------------------------
    # SELLING RATE CHECK
    # --------------------------------------------------------

    selling_rate = safe_float(
        memory.get("selling_rate")
    )

    if selling_rate is None or selling_rate <= 0:

        return {
            "success": False,
            "status": "waiting_for_selling_rate",
            "message": "selling rate کیا ہے؟"
        }

    # --------------------------------------------------------
    # TRANSPORT COST
    # --------------------------------------------------------

    transport_cost = safe_float(
        memory.get("transport_cost"),
        default=0
    )

    if transport_cost < 0:

        return {
            "success": False,
            "status": "invalid_transport_cost",
            "message": "Transport cost درست درج کریں۔"
        }

    # --------------------------------------------------------
    # CREATE SALE
    # --------------------------------------------------------

    result = create_sale_action(

        db=db,

        buyer_name=memory["buyer_name"],

        product_name=memory["product_name"],

        quantity=quantity,

        selling_rate=selling_rate,

        transport_cost=transport_cost,

        notes=memory.get("notes")
    )

    # --------------------------------------------------------
    # CLEAR MEMORY AFTER SUCCESS
    # --------------------------------------------------------

    if result.get("success"):

        sale_memory.pop(
            session_id,
            None
        )

    return result
