from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Notifikasi(Base):
    __tablename__ = "notifikasi"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pesan = Column(String(255), nullable=False)
    tipe = Column(String(30), default="status_update")
    pengajuan_id = Column(Integer, ForeignKey("pengajuan.id", ondelete="SET NULL"), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship(
        "User",
        back_populates="notifikasi_list",
        foreign_keys=[user_id],
    )
