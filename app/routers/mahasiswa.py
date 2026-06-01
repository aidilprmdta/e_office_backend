from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
import shutil
import os
import uuid

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.notifikasi import Notifikasi
from app.models.user import User
from app.schemas.pengajuan import PengajuanResponse, TrackingResponse, TimelineItem
from app.middleware.auth import require_role
from app.core.pengajuan_status import (
    normalize_status,
    PengajuanStatus,
)
from app.services.pengajuan_service import (
    log_status_change,
    notify_mahasiswa,
    create_initial_log,
    build_tracking_response,
)

router = APIRouter(
    prefix="/api/mahasiswa",
    tags=["Mahasiswa"]
)

UPLOAD_DIR = "uploads/"
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Format file tidak didukung")

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 5MB")



def _save_upload(file: UploadFile) -> str:
    validate_file(file)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = file.filename.replace(" ", "_")
    filename = f"{uuid.uuid4()}_{safe_name}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return filename


@router.post("/pengajuan", response_model=PengajuanResponse)
def buat_pengajuan(
    jenis_pengajuan: str = Form(...),
    judul_perihal: str = Form(...),
    kategori: Optional[str] = Form(None),
    deskripsi: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    jenis_pengajuan = jenis_pengajuan.strip()

    if jenis_pengajuan not in ["Surat", "Tugas Akhir"]:
        raise HTTPException(
            status_code=400,
            detail="jenis_pengajuan harus 'Surat' atau 'Tugas Akhir'"
        )

    file_url = None
    if file and file.filename:
        validate_file(file)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        safe_name = file.filename.replace(" ", "_")
        filename = f"{uuid.uuid4()}_{safe_name}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_url = filename

    pengajuan = Pengajuan(
        mahasiswa_id=current_user.id,
        jenis_pengajuan=jenis_pengajuan,
        judul_perihal=judul_perihal,
        kategori=kategori,
        deskripsi=deskripsi,
        file_url=file_url,
        status=PengajuanStatus.DIAJUKAN.value,
    )

    db.add(pengajuan)
    db.flush()
    create_initial_log(db, pengajuan, current_user.id)
    notify_reviewers(db, pengajuan, current_user)
    db.commit()
    db.refresh(pengajuan)
    return pengajuan


@router.get("/pengajuan")
def get_pengajuan_saya(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    """Ambil semua pengajuan milik mahasiswa yang sedang login"""
    return db.query(Pengajuan).filter(
        Pengajuan.mahasiswa_id == current_user.id
    ).order_by(Pengajuan.created_at.desc()).all()


@router.delete("/pengajuan/{id}")
def hapus_pengajuan(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa")),
):
    """Hapus pengajuan milik mahasiswa (hanya yang masih Pending)"""
    pengajuan = db.query(Pengajuan).filter(
        Pengajuan.id == id,
        Pengajuan.mahasiswa_id == current_user.id
    ).first()

    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    if pengajuan.status != "Pending":
        raise HTTPException(
            status_code=400,
            detail="Hanya pengajuan berstatus Pending yang dapat dihapus"
        )

    if pengajuan.file_url:
        file_path = os.path.join(UPLOAD_DIR, pengajuan.file_url)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(pengajuan)
    db.commit()
    return {"message": "Pengajuan berhasil dihapus"}
@router.get("/pengajuan/{id}/tracking")
def tracking_pengajuan(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    pengajuan = db.query(Pengajuan).filter(
        Pengajuan.id == id,
        Pengajuan.mahasiswa_id == current_user.id
    ).first()

    if not pengajuan:
        raise HTTPException(
            status_code=404,
            detail="Pengajuan tidak ditemukan"
        )

    return {
        "id": pengajuan.id,
        "judul_perihal": pengajuan.judul_perihal,
        "status": pengajuan.status,
        "catatan_dosen": pengajuan.catatan_dosen,
        "created_at": pengajuan.created_at
    }
@router.put("/pengajuan/{id}/revisi")
def kirim_revisi(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    return {"message": "Endpoint revisi belum diimplementasikan"}
