from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PengajuanCreate(BaseModel):
    jenis_pengajuan: str  # "Surat" atau "Tugas Akhir"
    judul_perihal: str
    deskripsi: Optional[str] = None

class PengajuanUpdate(BaseModel):
    status: str            # "disetujui" atau "ditolak"
    catatan_dosen: Optional[str] = None

class PengajuanResponse(BaseModel):
    id: int
    mahasiswa_id: int
    jenis_pengajuan: str
    judul_perihal: str
    deskripsi: Optional[str]
    file_url: Optional[str]
    status: str
    catatan_dosen: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
