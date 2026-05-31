from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PengajuanCreate(BaseModel):
    jenis_pengajuan: str
    kategori: Optional[str] = None
    judul_perihal: str
    deskripsi: Optional[str] = None

class PengajuanUpdate(BaseModel):
    status: str
    catatan_dosen: Optional[str] = None
    catatan_revisi: Optional[str] = None
    file_hasil_url: Optional[str] = None

class PengajuanResponse(BaseModel):
    id: int
    mahasiswa_id: int
    jenis_pengajuan: str
    kategori: Optional[str] = None
    judul_perihal: str
    deskripsi: Optional[str] = None
    file_url: Optional[str] = None
    status: str
    catatan_dosen: Optional[str] = None
    catatan_revisi: Optional[str] = None
    file_hasil_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True