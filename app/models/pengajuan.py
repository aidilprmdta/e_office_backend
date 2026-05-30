from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Pengajuan(Base):
    __tablename__ = "pengajuan"

    id = Column(Integer, primary_key=True, index=True)
    judul_perihal = Column(String(255), nullable=False)
    jenis_pengajuan = Column(String(50), nullable=False)
    kategori = Column(String(100))
    deskripsi = Column(String(255))
    mahasiswa_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_url = Column(String(255))
    file_hasil_url = Column(String(255))
    status = Column(String(50), default="diajukan")
    catatan_dosen = Column(String(255))
    catatan_revisi = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    mahasiswa = relationship(
        "User",
        back_populates="pengajuan_list",
        foreign_keys=[mahasiswa_id],
    )
    status_logs = relationship(
        "PengajuanStatusLog",
        back_populates="pengajuan",
        order_by="PengajuanStatusLog.created_at",
    )
