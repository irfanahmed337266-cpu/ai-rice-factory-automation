
from sqlalchemy import Column, Integer, Numeric, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)

    buyer_id = Column(Integer)

    product_id = Column(Integer)

    quantity = Column(Integer, nullable=False)

    cost_price = Column(
        Numeric(12, 2),
        nullable=True
    )

    cogs = Column(
        Numeric(14, 2),
        nullable=True
    )

    gross_profit = Column(
        Numeric(14, 2),
        nullable=True
    )

    selling_rate = Column(
        Numeric(12, 2)
    )

    transport_cost = Column(
        Numeric(12, 2)
    )

    total_amount = Column(
        Numeric(14, 2)
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
