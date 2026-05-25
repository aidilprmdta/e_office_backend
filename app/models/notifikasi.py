from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.config.database import Base

class Notifikasi(Base):
    __tablename__ = "notifikasi"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pesan = Column(String(255), nullable=False)
    # Default False = belum dibaca
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
