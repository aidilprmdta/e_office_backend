from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.user import User

router = APIRouter(prefix="/api/verifikasi", tags=["Verifikasi"])


@router.get("/{kode}")
def verifikasi_surat(kode: str, db: Session = Depends(get_db)):
    """
    Verifikasi keaslian surat berdasarkan kode QR.
    Format kode: EO-{id}-{mahasiswa_id}
    """
    kode = kode.strip().upper()

    # Parse format kode: EO-0001-9
    try:
        parts = kode.split("-")
        if len(parts) < 3 or parts[0] != "EO":
            raise ValueError("Format kode tidak valid")
        pengajuan_id = int(parts[1])
        mahasiswa_id = int(parts[2])
    except (ValueError, IndexError):
        return {
            "valid": False,
            "pesan": "Format kode tidak dikenali. Pastikan kode QR berasal dari dokumen resmi E-Office.",
        }

    pengajuan = db.query(Pengajuan).filter(
        Pengajuan.id == pengajuan_id,
        Pengajuan.mahasiswa_id == mahasiswa_id,
    ).first()

    if not pengajuan:
        return {
            "valid": False,
            "pesan": "Surat tidak ditemukan. Kode ini tidak terdaftar dalam sistem.",
        }

    # Ambil nama mahasiswa
    mahasiswa = db.query(User).filter(User.id == pengajuan.mahasiswa_id).first()

    return {
        "valid": True,
        "pesan": "Surat terverifikasi dan terdaftar resmi dalam sistem E-Office Kampus.",
        "kode_verifikasi": kode,
        "judul_perihal": pengajuan.judul_perihal,
        "kategori": pengajuan.kategori,
        "jenis_pengajuan": pengajuan.jenis_pengajuan,
        "status": pengajuan.status,
        "nama_mahasiswa": mahasiswa.nama if mahasiswa else None,
        "created_at": pengajuan.created_at,
    }
