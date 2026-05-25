from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.notifikasi import Notifikasi
from app.models.user import User
from app.schemas.pengajuan import PengajuanResponse, PengajuanUpdate
from app.middleware.auth import get_current_user, require_role
from typing import Optional
import shutil, os, uuid

router = APIRouter(prefix="/api/pengajuan", tags=["Pengajuan"])

UPLOAD_DIR = "uploads/"
# File yang diizinkan diupload
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file(file: UploadFile):
    """Validasi ekstensi dan ukuran file"""
    if file:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Format file tidak didukung. Gunakan: {', '.join(ALLOWED_EXTENSIONS)}"
            )

# ─── MAHASISWA ───────────────────────────────────────────────

@router.post("/", response_model=PengajuanResponse, status_code=status.HTTP_201_CREATED)
def buat_pengajuan(
    jenis_pengajuan: str = Form(..., description="Surat atau Tugas Akhir"),
    judul_perihal: str = Form(..., description="Judul TA / Perihal surat"),
    deskripsi: Optional[str] = Form(None, description="Abstrak atau alasan pengajuan"),
    file: Optional[UploadFile] = File(None, description="Upload PDF/DOC (opsional, maks 5MB)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    """
    [MAHASISWA] Buat pengajuan baru (surat atau judul TA).
    Status awal otomatis 'pending'.
    """
    # Validasi jenis_pengajuan
    if jenis_pengajuan not in ["Surat", "Tugas Akhir"]:
        raise HTTPException(status_code=400, detail="jenis_pengajuan harus 'Surat' atau 'Tugas Akhir'")

    # Proses upload file jika ada
    file_url = None
    if file and file.filename:
        validate_file(file)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        # Pakai UUID agar nama file tidak bentrok
        filename = f"{uuid.uuid4()}_{file.filename}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        file_url = filename  # Simpan hanya nama file, bukan full path

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

@router.get("/saya")
def get_pengajuan_saya(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    """[MAHASISWA] Lihat riwayat semua pengajuan milik sendiri"""
    hasil = db.query(Pengajuan).filter(
        Pengajuan.mahasiswa_id == current_user.id
    ).order_by(Pengajuan.created_at.desc()).all()
    return hasil

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def hapus_pengajuan(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("mahasiswa"))
):
    """
    [MAHASISWA] Hapus pengajuan milik sendiri.
    Hanya pengajuan berstatus 'pending' yang bisa dihapus.
    """
    pengajuan = db.query(Pengajuan).filter(
        Pengajuan.id == id,
        Pengajuan.mahasiswa_id == current_user.id
    ).first()

    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")
    if pengajuan.status != "pending":
        raise HTTPException(
            status_code=400,
            detail="Hanya pengajuan dengan status 'pending' yang bisa dihapus"
        )

    # Hapus file jika ada
    if pengajuan.file_url:
        file_path = os.path.join(UPLOAD_DIR, pengajuan.file_url)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(pengajuan)
    db.commit()
    return {"message": "Pengajuan berhasil dihapus"}

# ─── DOSEN / ADMIN ───────────────────────────────────────────

@router.get("/semua")
def get_semua_pengajuan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("dosen", "admin"))
):
    """
    [DOSEN/ADMIN] Lihat semua pengajuan masuk dari seluruh mahasiswa.
    Dilengkapi data nama & NIM mahasiswa.
    """
    hasil = db.query(Pengajuan, User).join(
        User, Pengajuan.mahasiswa_id == User.id
    ).order_by(Pengajuan.created_at.desc()).all()

    return [
        {
            "id": p.id,
            "mahasiswa_id": p.mahasiswa_id,
            "nama_mahasiswa": u.nama,
            "nim": u.username,
            "jenis_pengajuan": p.jenis_pengajuan,
            "judul_perihal": p.judul_perihal,
            "deskripsi": p.deskripsi,
            "file_url": p.file_url,
            "status": p.status,
            "catatan_dosen": p.catatan_dosen,
            "created_at": p.created_at,
        }
        for p, u in hasil
    ]

@router.put("/{id}")
def update_pengajuan(
    id: int,
    data: PengajuanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("dosen"))
):
    """
    [DOSEN] Setujui atau tolak pengajuan mahasiswa.
    Setelah aksi ini, notifikasi otomatis dikirim ke mahasiswa.
    """
    # Validasi status yang dikirim
    if data.status not in ["disetujui", "ditolak"]:
        raise HTTPException(status_code=400, detail="Status harus 'disetujui' atau 'ditolak'")

    pengajuan = db.query(Pengajuan).filter(Pengajuan.id == id).first()
    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    pengajuan.status = data.status
    pengajuan.catatan_dosen = data.catatan_dosen
    db.commit()

    # Otomatis kirim notifikasi ke mahasiswa yang bersangkutan
    status_text = "DISETUJUI ✅" if data.status == "disetujui" else "DITOLAK ❌"
    pesan = f"Pengajuan '{pengajuan.judul_perihal}' telah {status_text} oleh Dosen."
    if data.catatan_dosen:
        pesan += f" Catatan: {data.catatan_dosen}"

    notif = Notifikasi(user_id=pengajuan.mahasiswa_id, pesan=pesan)
    db.add(notif)
    db.commit()

    return {"message": f"Pengajuan berhasil {data.status}", "notifikasi_terkirim": True}

# ─── DOWNLOAD FILE ────────────────────────────────────────────

@router.get("/download/{filename}")
def download_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download file berkas pengajuan (bisa diakses mahasiswa, dosen, admin)"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File tidak ditemukan")
    return FileResponse(file_path, filename=filename)
