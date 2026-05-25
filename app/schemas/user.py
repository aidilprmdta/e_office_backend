from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str  # NIM untuk mahasiswa, NIDN untuk dosen
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

    model_config = {"from_attributes": True}
