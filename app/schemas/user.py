from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    nama: Optional[str] = None
    role: str  # mahasiswa / dosen / admin

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    nama: Optional[str]
    role: str

    class Config:
        from_attributes = True
