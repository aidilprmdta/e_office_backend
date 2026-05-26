from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os
import uuid

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.user import User
from app.schemas.pengajuan import PengajuanResponse
from app.middleware.auth import require_role

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

@router.post("/pengajuan", response_model=PengajuanResponse)
def buat_pengajuan(

    jenis_pengajuan: str = Form(...),
    judul_perihal: str = Form(...),
    kategori: Optional[str] = Form(None), 
    deskripsi: Optional[str] = Form(None),

    file: Optional[UploadFile] = File(None),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_role("mahasiswa")
    )
):

    # rapikan input
    jenis_pengajuan = jenis_pengajuan.strip()

    # validasi jenis pengajuan
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
        file_url=file_url
    )

    db.add(pengajuan)
    db.commit()
    db.refresh(pengajuan)

    return pengajuan


@router.get("/pengajuan")
def get_pengajuan_saya(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_role("mahasiswa")
    )
):

    return db.query(Pengajuan).filter(
        Pengajuan.mahasiswa_id == current_user.id
    ).all()
# Alias /me untuk kompatibilitas FE
@router.get("/pengajuan/me")
def get_pengajuan_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    return db.query(Pengajuan).filter(
        Pengajuan.mahasiswa_id == current_user.id
    ).all()
