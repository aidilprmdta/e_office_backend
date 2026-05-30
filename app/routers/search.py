from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.user import User
from app.schemas.pengajuan import SearchResultItem
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/search", tags=["Pencarian"])


def _route_hint(role: str, jenis: str) -> str:
    if role == "mahasiswa":
        return "/riwayat-pengajuan"
    if jenis == "Tugas Akhir":
        return "/tugas-akhir"
    return "/persetujuan"


@router.get("/", response_model=list[SearchResultItem])
def global_search(
    q: str = Query(..., min_length=1, max_length=100, description="Kata kunci pencarian"),
    jenis: Optional[str] = Query(None, description="Filter jenis: Surat | Tugas Akhir"),
    status: Optional[str] = Query(None, description="Filter status"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    term = q.strip()
    if not term:
        return []

    role = (current_user.role or "").lower()
    like = f"%{term}%"

    filters = [
        Pengajuan.judul_perihal.ilike(like),
        Pengajuan.kategori.ilike(like),
        Pengajuan.deskripsi.ilike(like),
        Pengajuan.kode_verifikasi.ilike(like),
        User.nama.ilike(like),
        User.username.ilike(like),
    ]
    if term.isdigit():
        filters.append(Pengajuan.id == int(term))

    query = (
        db.query(Pengajuan, User.nama.label("nama_mahasiswa"))
        .join(User, Pengajuan.mahasiswa_id == User.id)
        .filter(or_(*filters))
    )

    if role == "mahasiswa":
        query = query.filter(Pengajuan.mahasiswa_id == current_user.id)

    if jenis:
        query = query.filter(Pengajuan.jenis_pengajuan.ilike(jenis.strip()))

    if status:
        query = query.filter(func.lower(Pengajuan.status) == status.strip().lower())

    rows = query.order_by(Pengajuan.created_at.desc()).limit(limit).all()

    results: list[SearchResultItem] = []
    for p, nama_mhs in rows:
        results.append(
            SearchResultItem(
                tipe="pengajuan",
                id=p.id,
                judul=p.judul_perihal,
                subjudul=p.kategori,
                status=p.status,
                jenis_pengajuan=p.jenis_pengajuan,
                kategori=p.kategori,
                kode_verifikasi=p.kode_verifikasi,
                nama_mahasiswa=nama_mhs,
                created_at=p.created_at,
                route_hint=_route_hint(role, p.jenis_pengajuan or "Surat"),
            )
        )

    if role == "admin" and len(results) < limit:
        user_rows = (
            db.query(User)
            .filter(or_(User.nama.ilike(like), User.username.ilike(like)))
            .limit(limit - len(results))
            .all()
        )
        for u in user_rows:
            results.append(
                SearchResultItem(
                    tipe="user",
                    id=u.id,
                    judul=u.nama,
                    subjudul=f"@{u.username} · {u.role}",
                    route_hint="/users",
                )
            )

    return results
