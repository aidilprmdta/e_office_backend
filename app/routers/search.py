from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.user import User
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/")
def global_search(
    q: str = Query("", description="Kata kunci pencarian"),
    jenis: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Pengajuan)

    # Filter berdasarkan role
    if current_user.role == "mahasiswa":
        query = query.filter(Pengajuan.mahasiswa_id == current_user.id)

    # Filter pencarian kata kunci
    if q:
        query = query.filter(
            Pengajuan.judul_perihal.ilike(f"%{q}%") |
            Pengajuan.kategori.ilike(f"%{q}%") |
            Pengajuan.deskripsi.ilike(f"%{q}%")
        )

    if jenis:
        query = query.filter(Pengajuan.jenis_pengajuan == jenis)

    if status:
        query = query.filter(Pengajuan.status == status)

    results = query.order_by(Pengajuan.created_at.desc()).limit(limit).all()

    return [
        {
            "id": p.id,
            "judul_perihal": p.judul_perihal,
            "jenis_pengajuan": p.jenis_pengajuan,
            "kategori": p.kategori,
            "status": p.status,
            "created_at": p.created_at,
        }
        for p in results
    ]
