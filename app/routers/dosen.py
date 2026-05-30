from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.notifikasi import Notifikasi
from app.models.user import User
from app.schemas.pengajuan import PengajuanUpdate
from app.middleware.auth import require_role
from app.core.pengajuan_status import normalize_status, PengajuanStatus
from app.services.pengajuan_service import log_status_change, notify_mahasiswa

router = APIRouter(
    prefix="/api/dosen",
    tags=["Dosen"]
)

LEGACY_TO_NEW = {
    "pending": PengajuanStatus.DIAJUKAN.value,
    "disetujui": PengajuanStatus.SELESAI.value,
    "ditolak": PengajuanStatus.DITOLAK.value,
}


@router.get("/pengajuan")
def get_semua_pengajuan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("dosen", "admin")),
):
    results = (
        db.query(Pengajuan, User.nama)
        .outerjoin(User, Pengajuan.mahasiswa_id == User.id)
        .order_by(Pengajuan.created_at.desc())
        .all()
    )
    out = []
    for p, nama in results:
        out.append({
            "id": p.id,
            "mahasiswa_id": p.mahasiswa_id,
            "nama_mahasiswa": nama or f"Mahasiswa ID: {p.mahasiswa_id}",
            "jenis_pengajuan": p.jenis_pengajuan,
            "kategori": p.kategori,
            "judul_perihal": p.judul_perihal,
            "deskripsi": p.deskripsi,
            "file_url": p.file_url,
            "file_hasil_url": p.file_hasil_url,
            "status": normalize_status(p.status),
            "catatan_dosen": p.catatan_dosen,
            "catatan_revisi": p.catatan_revisi,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
        })
    return out


@router.put("/pengajuan/{id}")
def update_pengajuan(
    id: int,
    data: PengajuanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("dosen", "admin")),
):
    pengajuan = db.query(Pengajuan).filter(Pengajuan.id == id).first()

    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    raw_status = (data.status or "").strip().lower()
    new_status = LEGACY_TO_NEW.get(raw_status, raw_status)

    if new_status == PengajuanStatus.PERLU_REVISI.value:
        if not data.catatan_revisi or len(data.catatan_revisi.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Catatan revisi wajib minimal 10 karakter",
            )
        pengajuan.catatan_revisi = data.catatan_revisi.strip()

    valid_statuses = {s.value for s in PengajuanStatus}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Status tidak valid. Gunakan: {', '.join(sorted(valid_statuses))}",
        )

    old_status = normalize_status(pengajuan.status)
    pengajuan.status = new_status
    if data.catatan_dosen:
        pengajuan.catatan_dosen = data.catatan_dosen

    log_status_change(
        db,
        pengajuan.id,
        old_status,
        new_status,
        data.catatan_dosen or data.catatan_revisi,
        current_user.id,
    )

    jenis = pengajuan.jenis_pengajuan or "pengajuan"
    judul = pengajuan.judul_perihal or ""

    if new_status == PengajuanStatus.SELESAI.value:
        meta = {"file_url": pengajuan.file_hasil_url, "pengajuan_id": pengajuan.id}
        pesan = f"{jenis} '{judul}' telah selesai."
        notify_mahasiswa(db, pengajuan, "surat_selesai", pesan, meta)
    elif new_status == PengajuanStatus.DITOLAK.value:
        pesan = f"{jenis} '{judul}' ditolak."
        if data.catatan_dosen:
            pesan += f" Catatan: {data.catatan_dosen}"
        notify_mahasiswa(db, pengajuan, "status_update", pesan, {"pengajuan_id": pengajuan.id})
    elif new_status == PengajuanStatus.PERLU_REVISI.value:
        notify_mahasiswa(
            db,
            pengajuan,
            "revisi",
            f"{jenis} '{judul}' perlu revisi: {pengajuan.catatan_revisi[:200]}",
            {"pengajuan_id": pengajuan.id},
        )
    else:
        label = new_status.replace("_", " ").title()
        notify_mahasiswa(
            db,
            pengajuan,
            "status_update",
            f"{jenis} '{judul}' — status: {label}",
            {"pengajuan_id": pengajuan.id, "status": new_status},
        )

    db.commit()

    return {"message": "Status pengajuan berhasil diperbarui", "status": new_status}
