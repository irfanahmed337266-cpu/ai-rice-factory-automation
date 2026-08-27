from sqlalchemy import Column, Integer, Numeric, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)

    expense_type = Column(
        String(100),
        nullable=False
    )

    amount = Column(
        Numeric(14, 2),
        nullable=False
    )

    expense_date = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    payment_method = Column(
        String(50),
        default="Cash"
    )

    reference = Column(
        String(100),
        nullable=True
    )

    notes = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )