from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.supplier import Supplier


router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class SupplierCreate(BaseModel):
    name: str
    phone: str | None = None
    city: str | None = None
    address: str | None = None


@router.get("/")
def get_suppliers(db: Session = Depends(get_db)):
    suppliers = db.query(Supplier).all()
    return suppliers


@router.post("/")
def create_supplier(
    supplier: SupplierCreate,
    db: Session = Depends(get_db)
):
    new_supplier = Supplier(
        name=supplier.name,
        phone=supplier.phone,
        city=supplier.city,
        address=supplier.address
    )

    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)

    return new_supplier