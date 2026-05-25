from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PengajuanCreate(BaseModel):
    jenis_pengajuan: str
    kategori: str
    judul_perihal: str
    deskripsi: Optional[str] = None

class PengajuanUpdate(BaseModel):
    status: str
    catatan_dosen: Optional[str] = None

class PengajuanResponse(BaseModel):
    id: int
    mahasiswa_id: int
    jenis_pengajuan: str
    kategori: str
    judul_perihal: str
    deskripsi: Optional[str]
    file_url: Optional[str]
    status: str
    catatan_dosen: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True