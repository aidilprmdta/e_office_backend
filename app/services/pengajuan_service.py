from sqlalchemy.orm import Session

from app.models.pengajuan import Pengajuan
from app.models.pengajuan_status_log import PengajuanStatusLog
from app.models.notifikasi import Notifikasi
from app.core.pengajuan_status import PengajuanStatus, normalize_status


def log_status_change(
    db: Session,
    pengajuan_id: int,
    status_lama: str | None,
    status_baru: str,
    catatan: str | None,
    user_id: int | None,
) -> None:
    db.add(
        PengajuanStatusLog(
            pengajuan_id=pengajuan_id,
            status_lama=normalize_status(status_lama) if status_lama else None,
            status_baru=normalize_status(status_baru),
            catatan=catatan,
            diubah_oleh=user_id,
        )
    )


def notify_mahasiswa(
    db: Session,
    pengajuan: Pengajuan,
    tipe: str,
    pesan: str,
    metadata: dict | None = None,
) -> None:
    db.add(
        Notifikasi(
            user_id=pengajuan.mahasiswa_id,
            pesan=pesan[:255],
            tipe=tipe,
            pengajuan_id=pengajuan.id,
            metadata_json=metadata or {},
        )
    )


def create_initial_log(db: Session, pengajuan: Pengajuan, user_id: int) -> None:
    log_status_change(
        db,
        pengajuan.id,
        None,
        PengajuanStatus.DIAJUKAN.value,
        "Pengajuan dibuat",
        user_id,
    )


def build_tracking_response(db: Session, pengajuan: Pengajuan):
    from app.schemas.pengajuan import TrackingResponse, TimelineItem

    logs = (
        db.query(PengajuanStatusLog)
        .filter(PengajuanStatusLog.pengajuan_id == pengajuan.id)
        .order_by(PengajuanStatusLog.created_at.asc())
        .all()
    )
    timeline = [
        TimelineItem(status=l.status_baru, catatan=l.catatan, at=l.created_at)
        for l in logs
    ]
    return TrackingResponse(
        pengajuan_id=pengajuan.id,
        status_saat_ini=normalize_status(pengajuan.status),
        catatan_revisi=pengajuan.catatan_revisi,
        file_hasil_url=pengajuan.file_hasil_url,
        file_url=pengajuan.file_url,
        timeline=timeline,
    )
