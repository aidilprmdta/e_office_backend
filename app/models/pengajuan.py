from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
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
    status = Column(String(20), default="pending")
    catatan_dosen = Column(String(255))
    created_at = Column(DateTime, default=func.now())

    # Relasi ke mahasiswa pengaju
    mahasiswa = relationship(
        "User",
        back_populates="pengajuan_list",
        foreign_keys=[mahasiswa_id],
    )
