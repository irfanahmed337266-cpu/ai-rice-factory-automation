from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.purchase import Purchase
from app.models.material import Material
from app.models.supplier import Supplier
from app.models.inventory import Inventory

from app.models.sale import Sale
from app.models.buyer import Buyer
from app.models.product import Product

from app.models.payment import Payment
from app.models.expense import Expense


# ============================================================
# DECIMAL HELPERS
# ============================================================

def money(value) -> Decimal:
    """
    Convert a value to Decimal with 2 decimal places.
    This avoids floating-point calculation errors.
    """

    if value is None:
        return Decimal("0.00")

    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


# ============================================================
# CREATE PURCHASE ACTION
# ============================================================

def create_purchase_action(
    db: Session,
    supplier_name: str,
    material_name: str,
    quantity: int,
    purchase_rate: float | None = None,
    transport_cost: float | None = None,
    notes: str | None = None
):

    try:

        # ----------------------------------------------------
        # FIND SUPPLIER
        # ----------------------------------------------------

        supplier = db.query(Supplier).filter(
            Supplier.name.ilike(supplier_text)
        ).first()

        if not supplier:

            return {
                "success": False,
                "message": (
                    f"Supplier '{supplier_name}' "
                    "database میں نہیں ملا۔"
                )
            }

        # ----------------------------------------------------
        # FIND MATERIAL
        # ----------------------------------------------------

        material = db.query(Material).filter(
            Material.name.ilike(material_name)
        ).first()

        if not material:

            return {
                "success": False,
                "message": (
                    f"Material '{material_name}' "
                    "database میں نہیں ملا۔"
                )
            }

        # ----------------------------------------------------
        # VALIDATE QUANTITY
        # ----------------------------------------------------

        if quantity <= 0:

            return {
                "success": False,
                "message": (
                    "Purchase quantity صفر سے زیادہ ہونی چاہیے۔"
                )
            }

        # ----------------------------------------------------
        # MONEY VALUES
        # ----------------------------------------------------

        purchase_rate_decimal = (
            money(purchase_rate)
            if purchase_rate is not None
            else None
        )

        transport_decimal = (
            money(transport_cost)
            if transport_cost is not None
            else Decimal("0.00")
        )

        # ----------------------------------------------------
        # VALIDATE PURCHASE RATE
        # ----------------------------------------------------

        if purchase_rate_decimal is not None:

            if purchase_rate_decimal < 0:

                return {
                    "success": False,
                    "message": (
                        "Purchase rate منفی نہیں ہو سکتی۔"
                    )
                }

        # ----------------------------------------------------
        # VALIDATE TRANSPORT
        # ----------------------------------------------------

        if transport_decimal < 0:

            return {
                "success": False,
                "message": (
                    "Transport cost منفی نہیں ہو سکتی۔"
                )
            }

        # ----------------------------------------------------
        # CALCULATE TOTAL PURCHASE AMOUNT
        # ----------------------------------------------------

        total_amount = None

        if purchase_rate_decimal is not None:

            product_amount = (
                Decimal(quantity)
                * purchase_rate_decimal
            )

            total_amount = money(
                product_amount
                + transport_decimal
            )

        # ----------------------------------------------------
        # CREATE PURCHASE
        # ----------------------------------------------------

        purchase = Purchase(

            supplier_id=supplier.id,

            material_id=material.id,

            quantity=quantity,

            purchase_rate=purchase_rate_decimal,

            transport_cost=transport_decimal,

            total_amount=total_amount,

            availability_status="Available",

            payment_status="Pending",

            status="Pending",

            notes=notes
        )

        db.add(purchase)

        # ----------------------------------------------------
        # UPDATE RAW MATERIAL INVENTORY
        # ----------------------------------------------------

        inventory = db.query(Inventory).filter(
            Inventory.material_id == material.id
        ).first()

        # ====================================================
        # EXISTING INVENTORY
        # ====================================================

        if inventory:

            old_quantity = int(
                inventory.quantity or 0
            )

            old_rate = money(
                inventory.average_rate
            )

            new_quantity = (
                old_quantity + quantity
            )

            inventory.quantity = new_quantity

            # ------------------------------------------------
            # UPDATE WEIGHTED AVERAGE LANDED RATE
            # ------------------------------------------------

            if purchase_rate_decimal is not None:

                old_value = (
                    Decimal(old_quantity)
                    * old_rate
                )

                purchase_material_value = (
                    Decimal(quantity)
                    * purchase_rate_decimal
                )

                total_new_value = (
                    purchase_material_value
                    + transport_decimal
                )

                combined_value = (
                    old_value
                    + total_new_value
                )

                if new_quantity > 0:

                    inventory.average_rate = money(
                        combined_value
                        / Decimal(new_quantity)
                    )

        # ====================================================
        # NEW INVENTORY
        # ====================================================

        else:

            # ------------------------------------------------
            # Calculate landed cost per KG
            #
            # Example:
            #
            # Purchase rate = 100
            # Quantity      = 1000 KG
            # Transport     = 5000
            #
            # Transport per KG = 5
            #
            # Landed rate = 105
            # ------------------------------------------------

            if purchase_rate_decimal is not None:

                transport_per_unit = (
                    transport_decimal
                    / Decimal(quantity)
                )

                initial_landed_rate = money(
                    purchase_rate_decimal
                    + transport_per_unit
                )

            else:

                initial_landed_rate = Decimal("0.00")

            inventory = Inventory(

                material_id=material.id,

                quantity=quantity,

                average_rate=initial_landed_rate
            )

            db.add(inventory)

        # ----------------------------------------------------
        # COMMIT PURCHASE
        # ----------------------------------------------------

        db.commit()

        db.refresh(purchase)

        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return {

            "success": True,

            "purchase_id": purchase.id,

            "supplier": supplier.name,

            "material": material.name,

            "quantity": quantity,

            "purchase_rate": (
                float(purchase_rate_decimal)
                if purchase_rate_decimal is not None
                else None
            ),

            "transport_cost": float(
                transport_decimal
            ),

            "total_amount": (
                float(total_amount)
                if total_amount is not None
                else None
            ),

            "message": (
                f"{quantity} کلو {material.name} "
                f"کی purchase درج کر دی گئی ہے۔"
            )
        }

    except Exception as e:

        db.rollback()

        return {

            "success": False,

            "message": (
                f"Purchase save نہیں ہو سکی: {str(e)}"
            )
        }


# ============================================================
# CREATE SALE ACTION
# ============================================================

def create_sale_action(
    db: Session,
    buyer_name: str,
    product_name: str,
    quantity: int,
    selling_rate: float,
    transport_cost: float = 0,
    notes: str | None = None
):

    try:

        # ----------------------------------------------------
        # FIND BUYER
        # ----------------------------------------------------


        buyer = None

        buyer_text = str(buyer_name).strip()

        buyer_id = None

        if buyer_text.isdigit():
            buyer_id = int(buyer_text)

        elif buyer_text.lower().startswith("buyer "):
            possible_id = buyer_text.split(" ", 1)[1].strip()

            if possible_id.isdigit():
                buyer_id = int(possible_id)

        if buyer_id is not None:
            buyer = db.query(Buyer).filter(
                Buyer.id == buyer_id
            ).first()

        if not buyer:
            buyer = db.query(Buyer).filter(
                Buyer.name.ilike(buyer_text)
            ).first()

        if not buyer:
            return {
                "success": False,
                "message": (
                    f"Buyer '{buyer_name}' "
                    "database mein nahi mila."
                )
            }

        # ----------------------------------------------------
        # FIND FINISHED PRODUCT
        # ----------------------------------------------------

        product = None

        product_text = str(product_name).strip()

        product_id = None

        if product_text.isdigit():
            product_id = int(product_text)

        elif product_text.lower().startswith("product "):
            possible_id = product_text.split(" ", 1)[1].strip()

            if possible_id.isdigit():
                product_id = int(possible_id)

        if product_id is not None:
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

        if not product:
            product = db.query(Product).filter(
                Product.name.ilike(product_text)
            ).first()

        if not product:

            return {
                "success": False,
                "message": (
                    f"Finished product '{product_name}' "
                    "database میں نہیں ملا۔"
                )
            }
        # ----------------------------------------------------
        # VALIDATE QUANTITY
        # ----------------------------------------------------

        if quantity <= 0:

            return {
                "success": False,
                "message": (
                    "Sale quantity صفر سے زیادہ ہونی چاہیے۔"
                )
            }

        # ----------------------------------------------------
        # VALIDATE SELLING RATE
        # ----------------------------------------------------

        selling_rate_decimal = money(
            selling_rate
        )

        if selling_rate_decimal <= 0:

            return {
                "success": False,
                "message": (
                    "Selling rate صفر سے زیادہ ہونی چاہیے۔"
                )
            }

        # ----------------------------------------------------
        # VALIDATE TRANSPORT
        # ----------------------------------------------------

        transport_decimal = money(
            transport_cost
        )

        if transport_decimal < 0:

            return {
                "success": False,
                "message": (
                    "Transport cost منفی نہیں ہو سکتی۔"
                )
            }

        # ----------------------------------------------------
        # CHECK PRODUCT STOCK
        # ----------------------------------------------------

        current_stock = Decimal(
            str(product.stock_quantity or 0)
        )

        requested_quantity = Decimal(
            str(quantity)
        )

        if current_stock < requested_quantity:

            return {
                "success": False,
                "message": (
                    f"'{product.name}' کا stock "
                    f"صرف {current_stock} ہے، "
                    f"جبکہ {quantity} چاہیے۔"
                )
            }

        # ----------------------------------------------------
        # GET COST PRICE
        # ----------------------------------------------------

        cost_price = money(
            product.average_rate
        )

        # ----------------------------------------------------
        # CALCULATE COGS
        # ----------------------------------------------------

        cogs = money(
            requested_quantity
            * cost_price
        )

        # ----------------------------------------------------
        # SALES REVENUE
        # ----------------------------------------------------

        sales_revenue = money(
            requested_quantity
            * selling_rate_decimal
        )

        # ----------------------------------------------------
        # TOTAL CUSTOMER CHARGE
        # ----------------------------------------------------

        total_amount = money(
            sales_revenue
            + transport_decimal
        )

        # ----------------------------------------------------
        # GROSS PROFIT
        #
        # Transport is recorded separately as expense.
        #
        # Therefore:
        #
        # Sales Revenue - COGS
        # ----------------------------------------------------

        gross_profit = money(
            sales_revenue
            - cogs
        )

        # ----------------------------------------------------
        # CREATE SALE
        # ----------------------------------------------------

        sale = Sale(

            buyer_id=buyer.id,

            product_id=product.id,

            quantity=quantity,

            selling_rate=selling_rate_decimal,

            transport_cost=transport_decimal,

            total_amount=total_amount,

            cogs=cogs,

            cost_price=cost_price,

            gross_profit=gross_profit,

            payment_status="Pending",

            status="Pending",

            notes=notes
        )

        db.add(sale)

        # ----------------------------------------------------
        # FLUSH SALE
        #
        # Generates sale.id before commit.
        # ----------------------------------------------------

        db.flush()

        # ----------------------------------------------------
        # REDUCE FINISHED PRODUCT STOCK
        # ----------------------------------------------------

        new_stock = (
            current_stock
            - requested_quantity
        )

        product.stock_quantity = new_stock

        # ----------------------------------------------------
        # CREATE CUSTOMER RECEIVABLE
        # ----------------------------------------------------

        receivable = Payment(

            sale_id=sale.id,

            purchase_id=None,

            party_type="Customer",

            amount=total_amount,

            payment_method="Cash",

            payment_status="Pending",

            reference=f"SALE-{sale.id}",

            notes=(
                f"Receivable for sale "
                f"{sale.id} - {buyer.name}"
            )
        )

        db.add(receivable)

        # ----------------------------------------------------
        # CREATE TRANSPORT EXPENSE
        # ----------------------------------------------------

        if transport_decimal > 0:

            transport_expense = Expense(

                expense_type="Sales Transport",

                amount=transport_decimal,

                payment_method="Cash",

                reference=f"SALE-{sale.id}",

                notes=(
                    f"Transport cost for sale "
                    f"{sale.id} - {buyer.name}"
                )
            )

            db.add(
                transport_expense
            )

        # ----------------------------------------------------
        # FINAL COMMIT
        # ----------------------------------------------------

        db.commit()

        db.refresh(sale)

        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return {

            "success": True,

            "sale_id": sale.id,

            "buyer": buyer.name,

            "product": product.name,

            "quantity": quantity,

            "selling_rate": float(
                selling_rate_decimal
            ),

            "transport_cost": float(
                transport_decimal
            ),

            "sales_revenue": float(
                sales_revenue
            ),

            "total_amount": float(
                total_amount
            ),

            "cogs": float(
                cogs
            ),

            "gross_profit": float(
                gross_profit
            ),

            "remaining_stock": float(
                new_stock
            ),

            "receivable": float(
                total_amount
            ),

            "transport_expense": float(
                transport_decimal
            ),

            "payment_status": "Pending",

            "message": (
                f"{quantity} کلو {product.name} "
                f"کی sale {buyer.name} "
                "کے نام درج کر دی گئی ہے۔"
            )
        }

    except Exception as e:

        # ----------------------------------------------------
        # ROLLBACK EVERYTHING
        # ----------------------------------------------------

        db.rollback()

        return {

            "success": False,

            "message": (
                f"Sale save نہیں ہو سکی: {str(e)}"
            )
        }