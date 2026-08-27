from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Text,
    DateTime
)

from sqlalchemy.sql import func

from app.database import Base


class Payment(Base):

    __tablename__ = "payments"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = Column(
        Integer,
        primary_key=True
    )

    # =====================================================
    # PURCHASE / SALE
    # =====================================================

    purchase_id = Column(
        Integer,
        nullable=True
    )

    sale_id = Column(
        Integer,
        nullable=True
    )

    # =====================================================
    # PARTY
    # =====================================================

    party_type = Column(
        String(50),
        nullable=False
    )

    # =====================================================
    # AMOUNT
    # =====================================================

    amount = Column(
        Numeric(14, 2),
        nullable=False
    )

    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    payment_method = Column(
        String(50),
        default="Cash"
    )

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    payment_status = Column(
        String(50),
        default="Pending"
    )

    # =====================================================
    # PAYMENT DATE
    # =====================================================

    payment_date = Column(
        DateTime,
        server_default=func.current_timestamp()
    )

    # =====================================================
    # REFERENCE
    # =====================================================

    reference = Column(
        String(100),
        nullable=True
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # CREATED AT
    # =====================================================

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp()
    )