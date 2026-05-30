from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class PengajuanStatusLog(Base):
    __tablename__ = "pengajuan_status_log"

    id = Column(Integer, primary_key=True, index=True)
    pengajuan_id = Column(
        Integer,
        ForeignKey("pengajuan.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status_lama = Column(String(50))
    status_baru = Column(String(50), nullable=False)
    catatan = Column(Text)
    diubah_oleh = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    pengajuan = relationship("Pengajuan", back_populates="status_logs")
