from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.notifikasi import Notifikasi
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.notifikasi import NotifikasiResponse

router = APIRouter(prefix="/api/notifikasi", tags=["Notifikasi"])


@router.get("/", response_model=list[NotifikasiResponse])
def get_notifikasi(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notifikasi)
        .filter(Notifikasi.user_id == current_user.id)
        .order_by(Notifikasi.created_at.desc())
        .all()
    )


@router.get("/belum-dibaca")
def get_notifikasi_unread(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jumlah = (
        db.query(Notifikasi)
        .filter(
            Notifikasi.user_id == current_user.id,
            Notifikasi.is_read == False,
        )
        .count()
    )
    return {"belum_dibaca": jumlah}


@router.put("/{notif_id}/baca")
def baca_satu(
    notif_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = (
        db.query(Notifikasi)
        .filter(Notifikasi.id == notif_id, Notifikasi.user_id == current_user.id)
        .first()
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notifikasi tidak ditemukan")

    notif.is_read = True
    db.commit()
    return {"message": "Notifikasi ditandai sudah dibaca"}


@router.put("/baca-semua")
def baca_semua(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notifikasi).filter(
        Notifikasi.user_id == current_user.id,
        Notifikasi.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "Semua notifikasi sudah ditandai dibaca"}
