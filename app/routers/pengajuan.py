from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.notifikasi import Notifikasi
from app.schemas.pengajuan import PengajuanResponse, PengajuanUpdate
from app.middleware.auth import get_current_user, require_role
from app.models.user import User
from typing import Optional
import shutil, os, uuid

router = APIRouter(prefix="/api/pengajuan", tags=["Pengajuan"])
UPLOAD_DIR = "uploads/"

# Mahasiswa: buat pengajuan baru
@router.post("/", response_model=PengajuanResponse)
def buat_pengajuan(
    jenis_pengajuan: str = Form(...),
    judul_perihal: str = Form(...),
    deskripsi: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    file_url = None
    if file:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid.uuid4()}_{file.filename}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_url = path

    pengajuan = Pengajuan(
        mahasiswa_id=current_user.id,
        jenis_pengajuan=jenis_pengajuan,
        judul_perihal=judul_perihal,
        deskripsi=deskripsi,
        file_url=file_url
    )
    db.add(pengajuan)
    db.commit()
    db.refresh(pengajuan)
    return pengajuan

# Mahasiswa: lihat pengajuan milik sendiri
@router.get("/saya")
def get_pengajuan_saya(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    return db.query(Pengajuan).filter(Pengajuan.mahasiswa_id == current_user.id).all()

# Dosen/Admin: lihat semua pengajuan
@router.get("/semua")
def get_semua_pengajuan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("dosen", "admin"))
):
    return db.query(Pengajuan).all()

# Dosen: setujui atau tolak pengajuan
@router.put("/{id}")
def update_pengajuan(
    id: int,
    data: PengajuanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("dosen"))
):
    pengajuan = db.query(Pengajuan).filter(Pengajuan.id == id).first()
    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")
    
    pengajuan.status = data.status
    pengajuan.catatan_dosen = data.catatan_dosen
    db.commit()

    # Kirim notifikasi ke mahasiswa
    pesan = f"Pengajuan '{pengajuan.judul_perihal}' telah {data.status}."
    notif = Notifikasi(user_id=pengajuan.mahasiswa_id, pesan=pesan)
    db.add(notif)
    db.commit()

    return {"message": "Status pengajuan diperbarui"}

# Mahasiswa: hapus pengajuan (hanya yang masih pending)
@router.delete("/{id}")
def hapus_pengajuan(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    pengajuan = db.query(Pengajuan).filter(Pengajuan.id == id, Pengajuan.mahasiswa_id == current_user.id).first()
    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")
    if pengajuan.status != "pending":
        raise HTTPException(status_code=400, detail="Hanya pengajuan pending yang bisa dihapus")
    
    db.delete(pengajuan)
    db.commit()
    return {"message": "Pengajuan berhasil dihapus"}
