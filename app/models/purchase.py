from sqlalchemy import Column, Integer, Numeric, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True)

    supplier_id = Column(Integer)
    material_id = Column(Integer)

    quantity = Column(Integer, nullable=False)

    purchase_rate = Column(Numeric(12, 2))
    transport_cost = Column(Numeric(12, 2))
    total_amount = Column(Numeric(14, 2))

    availability_status = Column(
        String(50),
        default="Available"
    )

    payment_status = Column(
        String(50),
        default="Pending"
    )

    status = Column(
        String(50),
        default="Pending"
    )

    notes = Column(Text)

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )