from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, String
from sqlalchemy.sql import func

from app.database import Base


class Production(Base):
    __tablename__ = "production"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    input_material_id = Column(
        Integer,
        ForeignKey("materials.id"),
        nullable=False
    )

    output_product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    input_quantity = Column(
        Integer,
        nullable=False
    )

    output_quantity = Column(
        Integer,
        nullable=False
    )

    waste_quantity = Column(
        Integer,
        nullable=False,
        default=0
    )

    ml_predicted_yield_rate = Column(
        "predicted_yield_rate",
        Numeric,
        nullable=True
    )

    ml_predicted_output_quantity = Column(
        "predicted_output_quantity",
        Numeric,
        nullable=True
    )

    ml_predicted_waste_quantity = Column(
        "predicted_waste_quantity",
        Numeric,
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="Pending"
    )

    notes = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )