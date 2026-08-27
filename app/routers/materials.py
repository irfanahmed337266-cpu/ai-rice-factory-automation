from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.material import Material


router = APIRouter(
    prefix="/materials",
    tags=["Materials"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_materials(db: Session = Depends(get_db)):
    materials = db.query(Material).all()

    return materials