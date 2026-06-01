import os
import shutil
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.user import User
from app.schemas.pengajuan import StatusUpdateRequest, TrackingResponse
from app.middleware.auth import require_role
from app.core.pengajuan_status import (
    assert_transition,
    normalize_status,
    PengajuanStatus,
)
from app.services.pengajuan_service import (
    log_status_change,
    notify_mahasiswa,
    build_tracking_response,
)
from app.services.notify_channels import send_email, send_whatsapp_fonnte
from app.core.kode_verifikasi import assign_kode_if_needed

router = APIRouter(prefix="/api/admin", tags=["Admin Pengajuan"])

UPLOAD_DIR = "uploads/"
ALLOWED_EXTENSIONS = {".pdf"}


def _get_pengajuan_or_404(db: Session, pengajuan_id: int) -> Pengajuan:
    p = db.query(Pengajuan).filter(Pengajuan.id == pengajuan_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")
    return p


@router.put("/pengajuan/{pengajuan_id}/status")
async def update_status_surat(
    pengajuan_id: int,
    data: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "dosen")),
):
    p = _get_pengajuan_or_404(db, pengajuan_id)
    new_status = normalize_status(data.status)
    old_status = normalize_status(p.status)

    try:
        assert_transition(old_status, new_status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if new_status == PengajuanStatus.PERLU_REVISI.value:
        if not data.catatan_revisi or len(data.catatan_revisi.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Catatan revisi wajib minimal 10 karakter",
            )
        p.catatan_revisi = data.catatan_revisi.strip()

    if new_status == PengajuanStatus.SELESAI.value and not p.file_hasil_url:
        raise HTTPException(
            status_code=400,
            detail="Upload dokumen hasil terlebih dahulu sebelum menandai selesai",
        )

    p.status = new_status
    if data.catatan:
        p.catatan_dosen = data.catatan

    catatan_log = data.catatan or data.catatan_revisi
    log_status_change(db, p.id, old_status, new_status, catatan_log, current_user.id)

    if new_status == PengajuanStatus.PERLU_REVISI.value:
        notify_mahasiswa(
            db,
            p,
            "revisi",
            f"Surat '{p.judul_perihal}' perlu revisi: {p.catatan_revisi[:200]}",
            {"pengajuan_id": p.id},
        )
    elif new_status == PengajuanStatus.SELESAI.value:
        kode = assign_kode_if_needed(p)
        meta = {
            "file_url": p.file_hasil_url,
            "pengajuan_id": p.id,
            "judul": p.judul_perihal,
            "kode_verifikasi": kode,
        }
        pesan = (
            f"Surat '{p.judul_perihal}' telah selesai. "
            f"Kode verifikasi: {kode}. Dokumen digital tersedia untuk diunduh."
        )
        notify_mahasiswa(db, p, "surat_selesai", pesan, meta)
        mhs = db.query(User).filter(User.id == p.mahasiswa_id).first()
        if mhs:
            await send_whatsapp_fonnte(mhs.no_hp, pesan)
            await send_email(mhs.email, "Surat Selesai - E-Office", pesan)
    else:
        label = new_status.replace("_", " ").title()
        notify_mahasiswa(
            db,
            p,
            "status_update",
            f"Status surat '{p.judul_perihal}': {label}",
            {"pengajuan_id": p.id, "status": new_status},
        )

    db.commit()
    db.refresh(p)
    return {"message": "Status diperbarui", "status": p.status}


@router.post("/pengajuan/{pengajuan_id}/upload-hasil")
async def upload_surat_jadi(
    pengajuan_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "dosen")),
):
    p = _get_pengajuan_or_404(db, pengajuan_id)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Hanya file PDF yang diizinkan")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = (file.filename or "hasil.pdf").replace(" ", "_")
    filename = f"hasil_{uuid.uuid4()}_{safe_name}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    old_status = normalize_status(p.status)
    p.file_hasil_url = filename

    if old_status != PengajuanStatus.SELESAI.value:
        log_status_change(
            db,
            p.id,
            old_status,
            old_status,
            "Dokumen hasil diunggah admin",
            current_user.id,
        )

    meta = {
        "file_url": p.file_hasil_url,
        "pengajuan_id": p.id,
        "judul": p.judul_perihal,
    }
    notify_mahasiswa(
        db,
        p,
        "surat_selesai",
        f"Dokumen surat '{p.judul_perihal}' telah diunggah. Silakan unduh.",
        meta,
    )
    mhs = db.query(User).filter(User.id == p.mahasiswa_id).first()
    if mhs:
        pesan = f"Dokumen surat '{p.judul_perihal}' siap diunduh di E-Office Kampus."
        await send_whatsapp_fonnte(mhs.no_hp, pesan)
        await send_email(mhs.email, "Dokumen Surat Tersedia", pesan)

    db.commit()
    return {
        "message": "Dokumen hasil berhasil diunggah",
        "file_hasil_url": p.file_hasil_url,
    }


@router.get("/pengajuan/{pengajuan_id}/tracking", response_model=TrackingResponse)
def get_tracking_admin(
    pengajuan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "dosen")),
):
    p = _get_pengajuan_or_404(db, pengajuan_id)
    return build_tracking_response(db, p)
