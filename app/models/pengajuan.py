from sqlalchemy import Column, Integer, String, Text, Enum, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from app.config.database import Base

class Pengajuan(Base):
    __tablename__ = "pengajuan"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mahasiswa_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    jenis_pengajuan = Column(Enum("Surat", "Tugas Akhir"), nullable=False)
    judul_perihal = Column(String(255), nullable=False)
    deskripsi = Column(Text, nullable=True)
    file_url = Column(String(255), nullable=True)
    status = Column(Enum("pending", "disetujui", "ditolak"), default="pending")
    catatan_dosen = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
