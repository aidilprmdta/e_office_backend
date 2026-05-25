from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config.database import get_db
from app.models.user import User
from app.models.pengajuan import Pengajuan
from app.middleware.auth import require_role

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


# =====================================================
# DASHBOARD ADMIN
# =====================================================
@router.get("/dashboard")
def dashboard_admin(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_role("admin")
    )
):

    total_user = db.query(
        func.count(User.id)
    ).scalar()

    total_pengajuan = db.query(
        func.count(Pengajuan.id)
    ).scalar()

    total_pending = db.query(
        func.count(Pengajuan.id)
    ).filter(
        Pengajuan.status == "pending"
    ).scalar()

    total_disetujui = db.query(
        func.count(Pengajuan.id)
    ).filter(
        Pengajuan.status == "disetujui"
    ).scalar()

    total_ditolak = db.query(
        func.count(Pengajuan.id)
    ).filter(
        Pengajuan.status == "ditolak"
    ).scalar()

    return {
        "total_user": total_user,
        "total_pengajuan": total_pengajuan,
        "total_pending": total_pending,
        "total_disetujui": total_disetujui,
        "total_ditolak": total_ditolak
    }


# =====================================================
# GET ALL USERS
# =====================================================
@router.get("/users")
def get_all_users(

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_role("admin")
    )
):

    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "nama": user.nama,
            "role": user.role
        }
        for user in users
    ]