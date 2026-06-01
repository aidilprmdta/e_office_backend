"""Kode unik untuk verifikasi keaslian surat fisik (QR/barcode)."""
import secrets
from datetime import datetime

from app.models.pengajuan import Pengajuan
from app.core.pengajuan_status import normalize_status, PengajuanStatus


def generate_kode_verifikasi(pengajuan_id: int) -> str:
    year = datetime.now().year
    token = secrets.token_hex(3).upper()
    return f"EO-{year}-{pengajuan_id:04d}-{token}"


def assign_kode_if_needed(pengajuan: Pengajuan) -> str | None:
    """Generate kode saat surat selesai; kembalikan kode yang ada/dibuat."""
    if normalize_status(pengajuan.status) != PengajuanStatus.SELESAI.value:
        return pengajuan.kode_verifikasi

    if pengajuan.kode_verifikasi:
        return pengajuan.kode_verifikasi

    pengajuan.kode_verifikasi = generate_kode_verifikasi(pengajuan.id)
    return pengajuan.kode_verifikasi
