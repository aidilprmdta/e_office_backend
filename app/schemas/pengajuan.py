from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import datetime


class PengajuanCreate(BaseModel):
    jenis_pengajuan: str
    kategori: str
    judul_perihal: str
    deskripsi: Optional[str] = None


class PengajuanUpdate(BaseModel):
    status: str
    catatan_dosen: Optional[str] = None
    catatan_revisi: Optional[str] = None

    @field_validator("catatan_revisi")
    @classmethod
    def revisi_wajib_jika_perlu(cls, v, info):
        status = (info.data.get("status") or "").strip().lower()
        if status in ("perlu_revisi",) and (not v or len(v.strip()) < 10):
            raise ValueError("Catatan revisi wajib minimal 10 karakter")
        return v


class StatusUpdateRequest(BaseModel):
    status: str
    catatan: Optional[str] = None
    catatan_revisi: Optional[str] = None

    @field_validator("catatan_revisi")
    @classmethod
    def revisi_wajib(cls, v, info):
        status = (info.data.get("status") or "").strip().lower()
        if status == "perlu_revisi" and (not v or len(v.strip()) < 10):
            raise ValueError("Catatan revisi wajib minimal 10 karakter")
        return v


class TimelineItem(BaseModel):
    status: str
    catatan: Optional[str] = None
    at: datetime

    model_config = {"from_attributes": True}


class TrackingResponse(BaseModel):
    pengajuan_id: int
    status_saat_ini: str
    catatan_revisi: Optional[str] = None
    file_hasil_url: Optional[str] = None
    file_url: Optional[str] = None
    timeline: List[TimelineItem] = []


class PengajuanResponse(BaseModel):
    id: int
    mahasiswa_id: int
    jenis_pengajuan: str
    kategori: Optional[str] = None
    judul_perihal: str
    deskripsi: Optional[str] = None
    file_url: Optional[str] = None
    file_hasil_url: Optional[str] = None
    status: str
    catatan_dosen: Optional[str] = None
    catatan_revisi: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
