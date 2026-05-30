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


def notify_reviewers(db: Session, pengajuan: Pengajuan, mahasiswa: User):
    reviewers = db.query(User).filter(
        func.lower(User.role).in_(["dosen", "admin"])
    ).all()

    nama = mahasiswa.nama or mahasiswa.username
    pesan = (
        f"Pengajuan baru dari {nama}: "
        f"{pengajuan.judul_perihal} ({pengajuan.jenis_pengajuan})"
    )

    for reviewer in reviewers:
        db.add(
            Notifikasi(
                user_id=reviewer.id,
                pesan=pesan[:255],
                tipe="pengajuan_baru",
                pengajuan_id=pengajuan.id,
            )
        )


def validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Format file tidak didukung"
        )

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Ukuran file maksimal 5MB"
        )


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
    current_user: User = Depends(require_role("mahasiswa")),
):
    jenis_pengajuan = jenis_pengajuan.strip()

    if jenis_pengajuan not in ["Surat", "Tugas Akhir"]:
        raise HTTPException(
            status_code=400,
            detail="jenis_pengajuan harus 'Surat' atau 'Tugas Akhir'"
        )

    file_url = None
    if file and file.filename:
        file_url = _save_upload(file)

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
    current_user: User = Depends(require_role("mahasiswa")),
):
    return db.query(Pengajuan).filter(
        Pengajuan.mahasiswa_id == current_user.id
    ).order_by(Pengajuan.created_at.desc()).all()


@router.get("/pengajuan/me")
def get_pengajuan_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa")),
):
    return db.query(Pengajuan).filter(
        Pengajuan.mahasiswa_id == current_user.id
    ).order_by(Pengajuan.created_at.desc()).all()


@router.get("/pengajuan/{pengajuan_id}/tracking", response_model=TrackingResponse)
def get_tracking_mahasiswa(
    pengajuan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa")),
):
    p = db.query(Pengajuan).filter(
        Pengajuan.id == pengajuan_id,
        Pengajuan.mahasiswa_id == current_user.id,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")
    return build_tracking_response(db, p)


@router.put("/pengajuan/{pengajuan_id}/revisi", response_model=PengajuanResponse)
def kirim_revisi(
    pengajuan_id: int,
    judul_perihal: str = Form(...),
    kategori: Optional[str] = Form(None),
    deskripsi: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa")),
):
    p = db.query(Pengajuan).filter(
        Pengajuan.id == pengajuan_id,
        Pengajuan.mahasiswa_id == current_user.id,
    ).first()

    if not p:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    if normalize_status(p.status) != PengajuanStatus.PERLU_REVISI.value:
        raise HTTPException(
            status_code=400,
            detail="Hanya pengajuan berstatus perlu_revisi yang dapat direvisi",
        )

    old_status = p.status
    p.judul_perihal = judul_perihal
    p.kategori = kategori
    p.deskripsi = deskripsi

    if file and file.filename:
        if p.file_url:
            old_path = os.path.join(UPLOAD_DIR, p.file_url)
            if os.path.isfile(old_path):
                os.remove(old_path)
        p.file_url = _save_upload(file)

    p.catatan_revisi = None
    p.status = PengajuanStatus.DIAJUKAN.value

    log_status_change(
        db,
        p.id,
        old_status,
        PengajuanStatus.DIAJUKAN.value,
        "Revisi dikirim oleh mahasiswa",
        current_user.id,
    )
    notify_reviewers(db, p, current_user)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/pengajuan/{id}")
def hapus_pengajuan(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa")),
):
    pengajuan = db.query(Pengajuan).filter(
        Pengajuan.id == id,
        Pengajuan.mahasiswa_id == current_user.id
    ).first()

    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    status = normalize_status(pengajuan.status)
    allowed_delete = {
        PengajuanStatus.DIAJUKAN.value,
        PengajuanStatus.PERLU_REVISI.value,
        "pending",
    }
    if status not in allowed_delete:
        raise HTTPException(
            status_code=400,
            detail="Hanya pengajuan diajukan atau perlu revisi yang dapat dihapus"
        )

    if pengajuan.file_url:
        file_path = os.path.join(UPLOAD_DIR, pengajuan.file_url)
        if os.path.isfile(file_path):
            os.remove(file_path)

    db.delete(pengajuan)
    db.commit()

    return {"message": "Pengajuan berhasil dihapus"}
