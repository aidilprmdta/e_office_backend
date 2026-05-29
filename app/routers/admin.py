from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext

from app.config.database import get_db
from app.models.user import User
from app.models.pengajuan import Pengajuan
from app.schemas.user import UserCreate, UserAdminUpdate
from app.middleware.auth import require_role

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.get("/dashboard")
def dashboard_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    total_user = db.query(func.count(User.id)).scalar()
    total_pengajuan = db.query(func.count(Pengajuan.id)).scalar()

    total_pending = db.query(func.count(Pengajuan.id)).filter(
        func.lower(Pengajuan.status) == "pending"
    ).scalar()

    total_disetujui = db.query(func.count(Pengajuan.id)).filter(
        func.lower(Pengajuan.status) == "disetujui"
    ).scalar()

    total_ditolak = db.query(func.count(Pengajuan.id)).filter(
        func.lower(Pengajuan.status) == "ditolak"
    ).scalar()

    return {
        "total_user": total_user,
        "total_pengajuan": total_pengajuan,
        "total_pending": total_pending,
        "total_disetujui": total_disetujui,
        "total_ditolak": total_ditolak
    }

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
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


@router.post("/users")
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    allowed_roles = ["mahasiswa", "dosen", "admin"]
    if data.role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Role tidak valid")

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah dipakai")

    new_user = User(
        username=data.username,
        password=hash_password(data.password),
        nama=data.nama,
        role=data.role.strip().lower()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User berhasil dibuat",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "nama": new_user.nama,
            "role": new_user.role
        }
    }


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if data.role not in ["mahasiswa", "dosen", "admin"]:
        raise HTTPException(status_code=400, detail="Role tidak valid")

    if data.nama is not None:
        user.nama = data.nama
    user.role = data.role
    if data.password:
        user.password = hash_password(data.password)

    db.commit()
    db.refresh(user)

    return {
        "message": "User berhasil diperbarui",
        "user": {
            "id": user.id,
            "username": user.username,
            "nama": user.nama,
            "role": user.role
        }
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Tidak dapat menghapus akun sendiri")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    db.delete(user)
    db.commit()

    return {"message": "User berhasil dihapus"}
