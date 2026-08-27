from sqlalchemy import Column, Integer, Numeric, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Payable(Base):
    __tablename__ = "payables"

    id = Column(Integer, primary_key=True)

    purchase_id = Column(Integer, nullable=False)

    supplier_id = Column(Integer, nullable=False)

    total_amount = Column(Numeric(14, 2), nullable=False)

    paid_amount = Column(
        Numeric(14, 2),
        default=0
    )

    payable_amount = Column(
        Numeric(14, 2),
        nullable=False
    )

    payment_status = Column(
        String(50),
        default="Pending"
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )