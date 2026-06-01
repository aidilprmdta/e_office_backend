from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.config.database import Base


class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    password = Column(
        String,
        nullable=False
    )

    nama = Column(
        String,
        nullable=True
    )

    role = Column(
        String,
        nullable=False
    )

    email = Column(String(120), nullable=True)
    no_hp = Column(String(20), nullable=True)

    pengajuan_list = relationship(
        "Pengajuan",
        back_populates="mahasiswa",
        foreign_keys="Pengajuan.mahasiswa_id",
    )

    notifikasi_list = relationship(
        "Notifikasi",
        back_populates="user",
        foreign_keys="Notifikasi.user_id",
    )
