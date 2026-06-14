from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.config.database import get_db
from app.models.user import User
from app.models.pengajuan import Pengajuan
from app.schemas.user import UserCreate, UserUpdate, UserAdminUpdate
from app.middleware.auth import require_role
import shutil
import os
import uuid

router = APIRouter(prefix="/api/admin", tags=["Admin"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# =====================================================
# DASHBOARD
# =====================================================
@router.get("/dashboard")
def dashboard_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    total_user = db.query(func.count(User.id)).scalar()
    total_pengajuan = db.query(func.count(Pengajuan.id)).scalar()
    total_pending = db.query(func.count(Pengajuan.id)).filter(Pengajuan.status == "Pending").scalar()
    total_disetujui = db.query(func.count(Pengajuan.id)).filter(Pengajuan.status == "Disetujui").scalar()
    total_ditolak = db.query(func.count(Pengajuan.id)).filter(Pengajuan.status == "Ditolak").scalar()

    return {
        "total_user": total_user,
        "total_pengajuan": total_pengajuan,
        "total_pending": total_pending,
        "total_disetujui": total_disetujui,
        "total_ditolak": total_ditolak,
    }


# =====================================================
# ANALYTICS (untuk chart di DashboardAdmin)
# =====================================================
@router.get("/analytics")
def dashboard_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    bulan: int = 12,
):
    """Grafik beban surat per bulan & distribusi kategori (admin)."""
    bulan = max(3, min(bulan, 24))
    since = datetime.utcnow() - timedelta(days=bulan * 31)

    surat_rows = (
        db.query(Pengajuan)
        .filter(
            Pengajuan.created_at >= since,
            func.lower(Pengajuan.jenis_pengajuan) == "surat",
        )
        .all()
    )

    monthly: dict[str, int] = defaultdict(int)
    categories: dict[str, int] = defaultdict(int)

    for p in surat_rows:
        if p.created_at:
            key = p.created_at.strftime("%Y-%m")
            monthly[key] += 1
        kat = (p.kategori or "Lainnya").strip() or "Lainnya"
        categories[kat] += 1

    sorted_months = sorted(monthly.keys())[-bulan:]
    beban_bulanan = [
        {"bulan": m, "label": _bulan_label(m), "jumlah": monthly.get(m, 0)}
        for m in sorted_months
    ]

    total_kat = sum(categories.values()) or 1
    distribusi_kategori = [
        {
            "kategori": k,
            "jumlah": v,
            "persen": round((v / total_kat) * 100, 1),
        }
        for k, v in sorted(categories.items(), key=lambda x: -x[1])
    ]

    return {
        "beban_bulanan": beban_bulanan,
        "distribusi_kategori": distribusi_kategori,
        "total_surat_periode": len(surat_rows),
    }


def _bulan_label(ym: str) -> str:
    months_id = [
        "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
        "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
    ]
    try:
        y, m = ym.split("-")
        return f"{months_id[int(m) - 1]} {y}"
    except (ValueError, IndexError):
        return ym


@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "nama": u.nama, "role": u.role} for u in users]


# =====================================================
# CREATE USER
# =====================================================
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

    hashed = pwd_context.hash(data.password)
    new_user = User(username=data.username, password=hashed, nama=data.nama, role=data.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User berhasil dibuat", "user": {"id": new_user.id, "username": new_user.username, "nama": new_user.nama, "role": new_user.role}}


# =====================================================
# UPDATE USER
# =====================================================
@router.put("/users/{id}")
def update_user(
    id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    if data.nama is not None:
        user.nama = data.nama
    if data.role is not None:
        if data.role not in ["mahasiswa", "dosen", "admin"]:
            raise HTTPException(status_code=400, detail="Role tidak valid")
        user.role = data.role
    if data.password:
        user.password = pwd_context.hash(data.password)

    db.commit()
    db.refresh(user)
    return {"message": "User berhasil diperbarui", "user": {"id": user.id, "username": user.username, "nama": user.nama, "role": user.role}}


# =====================================================
# DELETE USER
# =====================================================
@router.delete("/users/{id}")
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    if id == current_user.id:
        raise HTTPException(status_code=400, detail="Tidak bisa menghapus akun sendiri")

    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User tidak ditemukan")

    db.delete(user)
    db.commit()
    return {"message": f"User '{user.username}' berhasil dihapus"}


# =====================================================
# GET ALL PENGAJUAN
# =====================================================
@router.get("/pengajuan")
def get_semua_pengajuan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "dosen"))
):
    return db.query(Pengajuan).order_by(Pengajuan.created_at.desc()).all()


@router.put("/pengajuan/{id}/status")
def update_status_pengajuan(
    id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "dosen"))
):
    pengajuan = db.query(Pengajuan).filter(Pengajuan.id == id).first()
    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    pengajuan.status = data.get("status", pengajuan.status)
    db.commit()
    db.refresh(pengajuan)

    return {
        "message": "Status berhasil diperbarui",
        "data": pengajuan
    }


@router.get("/pengajuan/{id}/tracking")
def get_tracking_pengajuan(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "dosen"))
):
    pengajuan = db.query(Pengajuan).filter(Pengajuan.id == id).first()
    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    return {
        "id": pengajuan.id,
        "judul_perihal": pengajuan.judul_perihal,
        "status": pengajuan.status,
        "created_at": pengajuan.created_at,
        "catatan_dosen": pengajuan.catatan_dosen,
        "jenis_pengajuan": pengajuan.jenis_pengajuan
    }
@router.post("/pengajuan/{id}/upload-hasil")
def upload_hasil(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "dosen"))
):
    pengajuan = db.query(Pengajuan).filter(Pengajuan.id == id).first()
    if not pengajuan:
        raise HTTPException(status_code=404, detail="Pengajuan tidak ditemukan")

    os.makedirs("uploads", exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join("uploads", filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    pengajuan.file_hasil_url = filename
    db.commit()

    return {"message": "File hasil berhasil diupload", "file_url": filename}
