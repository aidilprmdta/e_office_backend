from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models import Pengajuan #
from app.schemas.pengajuan import PengajuanResponse, PengajuanCreate
from app.routers.auth import get_current_user
from app.models.pengajuan import Pengajuan

router = APIRouter(prefix="/api/mahasiswa", tags=["Mahasiswa"])

@router.get("/pengajuan/me", response_model=list[PengajuanResponse])
def get_my_pengajuan(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Mengambil data pengajuan milik user yang sedang login
    pengajuan = db.query(Pengajuan).filter(Pengajuan.user_id == current_user.id).all()
    return pengajuan

@router.post("/pengajuan")
def create_pengajuan(
    judul_perihal: str,
    jenis_pengajuan: str,
    kategori: str,
    deskripsi: str,
    # ... handle file upload di sini
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Logika simpan ke database
    return {"message": "Pengajuan berhasil"}