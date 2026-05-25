from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.config.database import get_db
from app.models.user import User
from app.models.pengajuan import Pengajuan
from app.schemas.user import UserCreate, UserResponse
from app.middleware.auth import require_role
from passlib.context import CryptContext

router = APIRouter(prefix="/api/admin", tags=["Admin"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── DASHBOARD STATS ──────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """
    [ADMIN] Ambil data ringkasan untuk Card Stats di dashboard:
    - Total mahasiswa
    - Total dosen
    - Total pengajuan selesai (disetujui + ditolak)
    - Total pengajuan pending
    """
    total_mahasiswa = db.query(func.count(User.id)).filter(User.role == "mahasiswa").scalar()
    total_dosen = db.query(func.count(User.id)).filter(User.role == "dosen").scalar()
    total_selesai = db.query(func.count(Pengajuan.id)).filter(
        Pengajuan.status.in_(["disetujui", "ditolak"])
    ).scalar()
    total_pending = db.query(func.count(Pengajuan.id)).filter(
        Pengajuan.status == "pending"
    ).scalar()

    return {
        "total_mahasiswa": total_mahasiswa,
        "total_dosen": total_dosen,
        "total_pengajuan_selesai": total_selesai,
        "total_pengajuan_pending": total_pending,
    }

# ─── MANAJEMEN USER ───────────────────────────────────────────

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """[ADMIN] Lihat daftar semua akun (mahasiswa & dosen) yang terdaftar"""
    users = db.query(User).filter(User.role != "admin").order_by(User.role, User.nama).all()
    return [UserResponse.model_validate(u) for u in users]

@router.post("/users", status_code=status.HTTP_201_CREATED)
def tambah_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """[ADMIN] Tambah akun user baru (mahasiswa atau dosen)"""
    allowed_roles = ["mahasiswa", "dosen"]
    if data.role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Admin hanya bisa tambah role mahasiswa atau dosen")

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah dipakai")

    hashed = pwd_context.hash(data.password)
    user = User(username=data.username, password=hashed, nama=data.nama, role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User berhasil ditambahkan", "user": UserResponse.model_validate(user)}

@router.delete("/users/{id}")
def hapus_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """[ADMIN] Hapus akun user beserta seluruh pengajuannya"""
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="Tidak bisa menghapus akun admin")

    db.delete(user)
    db.commit()
    return {"message": f"Akun '{user.nama}' berhasil dihapus"}
