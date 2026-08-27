from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    unit = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.current_timestamp())