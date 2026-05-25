from sqlalchemy import Column, Integer, String, Enum
from app.config.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nama = Column(String(100), nullable=True)
    role = Column(Enum("mahasiswa", "dosen", "admin"), nullable=False)
