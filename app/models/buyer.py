from sqlalchemy import Column, Integer, String

from app.database import Base


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(50))
    city = Column(String(100))
    address = Column(String(255))