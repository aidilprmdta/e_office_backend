from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.notifikasi import Notifikasi
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/notifikasi", tags=["Notifikasi"])

@router.get("/")
def get_notifikasi(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lihat semua notifikasi milik user yang sedang login (terbaru di atas)"""
    return db.query(Notifikasi).filter(
        Notifikasi.user_id == current_user.id
    ).order_by(Notifikasi.created_at.desc()).all()

@router.get("/belum-dibaca")
def get_notifikasi_unread(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Ambil jumlah notifikasi yang belum dibaca (untuk badge/counter di FE)"""
    jumlah = db.query(Notifikasi).filter(
        Notifikasi.user_id == current_user.id,
        Notifikasi.is_read == False
    ).count()
    return {"belum_dibaca": jumlah}

@router.put("/baca-semua")
def baca_semua(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tandai semua notifikasi milik user ini sebagai sudah dibaca"""
    db.query(Notifikasi).filter(
        Notifikasi.user_id == current_user.id,
        Notifikasi.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Semua notifikasi sudah ditandai dibaca"}
