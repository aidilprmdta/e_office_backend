from pydantic import BaseModel
from typing import Literal

# Skema data saat user melakukan registrasi
class UserCreate(BaseModel):
    username: str
    password: str
    nama: str
    role: Literal['mahasiswa', 'dosen', 'admin'] [cite: 3]

# Skema data saat user melakukan login
class UserLogin(BaseModel):
    username: str
    password: str

# Skema data yang dikembalikan ke Frontend (tanpa password)
class UserResponse(BaseModel):
    id: int
    username: str
    nama: str
    role: str

    class Config:
        from_attributes = True