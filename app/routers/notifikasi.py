from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.notifikasi import Notifikasi
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/notifikasi", tags=["Notifikasi"])

# Lihat notifikasi milik sendiri
@router.get("/")
def get_notifikasi(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Notifikasi).filter(Notifikasi.user_id == current_user.id).order_by(Notifikasi.created_at.desc()).all()

# Tandai semua notifikasi sudah dibaca
@router.put("/baca-semua")
def baca_semua(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(Notifikasi).filter(
        Notifikasi.user_id == current_user.id,
        Notifikasi.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"message": "Semua notifikasi sudah dibaca"}
