from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.user import User
from app.schemas.pengajuan import VerifikasiSuratResponse
from app.core.pengajuan_status import normalize_status, PengajuanStatus

router = APIRouter(prefix="/api/verifikasi", tags=["Verifikasi Surat"])


def _normalize_kode(raw: str) -> str:
    return raw.strip().upper().replace(" ", "")


@router.get("/{kode}", response_model=VerifikasiSuratResponse)
def verifikasi_surat(kode: str, db: Session = Depends(get_db)):
    """Endpoint publik — verifikasi keaslian surat via kode QR/barcode."""
    kode_norm = _normalize_kode(kode)
    if len(kode_norm) < 6:
        raise HTTPException(status_code=400, detail="Format kode tidak valid")

    row = (
        db.query(Pengajuan, User.nama.label("nama_mahasiswa"))
        .join(User, Pengajuan.mahasiswa_id == User.id)
        .filter(Pengajuan.kode_verifikasi == kode_norm)
        .first()
    )

    if not row:
        return VerifikasiSuratResponse(
            valid=False,
            pesan="Kode tidak ditemukan dalam sistem. Surat mungkin palsu atau belum terdaftar.",
        )

    p, nama_mhs = row
    status = normalize_status(p.status)

    if status != PengajuanStatus.SELESAI.value:
        return VerifikasiSuratResponse(
            valid=False,
            pesan=f"Surat terdaftar tetapi belum selesai (status: {status.replace('_', ' ')}).",
            kode_verifikasi=p.kode_verifikasi,
            judul_perihal=p.judul_perihal,
            jenis_pengajuan=p.jenis_pengajuan,
            kategori=p.kategori,
            status=status,
            nama_mahasiswa=nama_mhs,
            tanggal_pengajuan=p.created_at,
        )

    return VerifikasiSuratResponse(
        valid=True,
        pesan="Surat terverifikasi — dokumen terdaftar resmi di E-Office Kampus.",
        kode_verifikasi=p.kode_verifikasi,
        judul_perihal=p.judul_perihal,
        jenis_pengajuan=p.jenis_pengajuan,
        kategori=p.kategori,
        status=status,
        nama_mahasiswa=nama_mhs,
        tanggal_pengajuan=p.created_at,
        tanggal_selesai=p.updated_at or p.created_at,
    )
