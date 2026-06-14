from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.config.database import Base


class Pengajuan(Base):
    __tablename__ = "pengajuan"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mahasiswa_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    jenis_pengajuan = Column(String(50), nullable=False)
    judul_perihal = Column(String(255), nullable=False)
    deskripsi = Column(Text, nullable=True)
    file_url = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")
    catatan_dosen = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    kategori = Column(String(100), nullable=True)
    catatan_revisi = Column(Text, nullable=True)
    file_hasil_url = Column(String(255), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    kode_verifikasi = Column(String(32), nullable=True)

    mahasiswa = relationship(
        "User",
        back_populates="pengajuan_list",
        foreign_keys=[mahasiswa_id],
    )

    status_logs = relationship(
        "PengajuanStatusLog",
        back_populates="pengajuan",
        cascade="all, delete-orphan",
    )
