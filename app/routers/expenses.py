from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.expense import Expense


router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"]
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
# SCHEMAS
# =========================================================

class ExpenseCreate(BaseModel):

    expense_type: str

    amount: float

    expense_date: datetime | None = None

    payment_method: str = "Cash"

    reference: str | None = None

    notes: str | None = None


class ExpenseUpdate(BaseModel):

    expense_type: str

    amount: float

    expense_date: datetime | None = None

    payment_method: str = "Cash"

    reference: str | None = None

    notes: str | None = None


# =========================================================
# VALIDATE EXPENSE
# =========================================================

def validate_expense(expense):

    # =====================================================
    # EXPENSE TYPE
    # =====================================================

    expense_type = expense.expense_type.strip()

    if not expense_type:

        raise HTTPException(
            status_code=400,
            detail="Expense type is required"
        )

    # =====================================================
    # AMOUNT
    # =====================================================

    if expense.amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Expense amount must be greater than 0"
        )

    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    payment_method = expense.payment_method.strip()

    if not payment_method:

        raise HTTPException(
            status_code=400,
            detail="Payment method is required"
        )

    return {
        "expense_type": expense_type,
        "payment_method": payment_method
    }


# =========================================================
# GET ALL EXPENSES
# =========================================================

@router.get("/")
def get_expenses(
    db: Session = Depends(get_db)
):

    return db.query(
        Expense
    ).order_by(
        Expense.id.desc()
    ).all()


# =========================================================
# GET SINGLE EXPENSE
# =========================================================

@router.get("/{expense_id}")
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):

    expense = db.query(
        Expense
    ).filter(
        Expense.id == expense_id
    ).first()

    if not expense:

        raise HTTPException(
            status_code=404,
            detail=f"Expense {expense_id} not found"
        )

    return expense


# =========================================================
# CREATE EXPENSE
# =========================================================

@router.post("/")
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db)
):

    # =====================================================
    # VALIDATE
    # =====================================================

    validated = validate_expense(
        expense
    )

    # =====================================================
    # CREATE
    # =====================================================

    new_expense = Expense(

        expense_type=validated["expense_type"],

        amount=expense.amount,

        payment_method=validated["payment_method"],

        reference=expense.reference,

        notes=expense.notes
    )

    # =====================================================
    # OPTIONAL DATE
    # =====================================================

    if expense.expense_date is not None:

        new_expense.expense_date = (
            expense.expense_date
        )

    # =====================================================
    # SAVE
    # =====================================================

    try:

        db.add(new_expense)

        db.commit()

        db.refresh(new_expense)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Expense could not be created."
        )

    return new_expense


# =========================================================
# UPDATE EXPENSE
# =========================================================

@router.put("/{expense_id}")
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db)
):

    # =====================================================
    # FIND EXPENSE
    # =====================================================

    existing_expense = db.query(
        Expense
    ).filter(
        Expense.id == expense_id
    ).first()

    if not existing_expense:

        raise HTTPException(
            status_code=404,
            detail=f"Expense {expense_id} not found"
        )

    # =====================================================
    # VALIDATE
    # =====================================================

    validated = validate_expense(
        expense
    )

    # =====================================================
    # UPDATE
    # =====================================================

    existing_expense.expense_type = (
        validated["expense_type"]
    )

    existing_expense.amount = (
        expense.amount
    )

    existing_expense.payment_method = (
        validated["payment_method"]
    )

    existing_expense.reference = (
        expense.reference
    )

    existing_expense.notes = (
        expense.notes
    )

    # =====================================================
    # UPDATE DATE
    # =====================================================

    if expense.expense_date is not None:

        existing_expense.expense_date = (
            expense.expense_date
        )

    # =====================================================
    # SAVE
    # =====================================================

    try:

        db.commit()

        db.refresh(existing_expense)

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Expense could not be updated."
        )

    return existing_expense


# =========================================================
# DELETE EXPENSE
# =========================================================

@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):

    # =====================================================
    # FIND EXPENSE
    # =====================================================

    expense = db.query(
        Expense
    ).filter(
        Expense.id == expense_id
    ).first()

    if not expense:

        raise HTTPException(
            status_code=404,
            detail=f"Expense {expense_id} not found"
        )

    # =====================================================
    # DELETE
    # =====================================================

    try:

        db.delete(expense)

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Expense could not be deleted."
        )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "success": True,
        "message": (
            f"Expense {expense_id} "
            "deleted successfully"
        ),
        "expense_id": expense_id
    }