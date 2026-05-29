from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.pengajuan import Pengajuan
from app.models.notifikasi import Notifikasi
from app.models.user import User
from app.schemas.pengajuan import PengajuanUpdate
from app.middleware.auth import require_role

router = APIRouter(
    prefix="/api/dosen",
    tags=["Dosen"]
)


@router.get("/pengajuan")
def get_semua_pengajuan(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("dosen", "admin")
    )
):
    results = db.query(Pengajuan, User.nama).outerjoin(User, Pengajuan.mahasiswa_id == User.id).all()
    out = []
    for p, nama in results:
        p_dict = {
            "id": p.id,
            "mahasiswa_id": p.mahasiswa_id,
            "nama_mahasiswa": nama or f"Mahasiswa ID: {p.mahasiswa_id}",
            "jenis_pengajuan": p.jenis_pengajuan,
            "kategori": p.kategori,
            "judul_perihal": p.judul_perihal,
            "deskripsi": p.deskripsi,
            "file_url": p.file_url,
            "status": p.status,
            "catatan_dosen": p.catatan_dosen,
            "created_at": p.created_at
        }
        out.append(p_dict)
    return out


@router.put("/pengajuan/{id}")
def update_pengajuan(

    id: int,

    data: PengajuanUpdate,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_role("dosen", "admin")
    )
):

    pengajuan = db.query(Pengajuan).filter(
        Pengajuan.id == id
    ).first()

    if not pengajuan:
        raise HTTPException(
            status_code=404,
            detail="Pengajuan tidak ditemukan"
        )

    status = (data.status or "").strip().lower()
    if status not in ("disetujui", "ditolak", "pending"):
        raise HTTPException(
            status_code=400,
            detail="Status harus 'disetujui', 'ditolak', atau 'pending'"
        )

    pengajuan.status = status
    pengajuan.catatan_dosen = data.catatan_dosen

    db.commit()

    jenis = pengajuan.jenis_pengajuan or "pengajuan"
    judul = pengajuan.judul_perihal or ""
    status_label = "disetujui" if status == "disetujui" else "ditolak"
    pesan = f"{jenis} '{judul}' telah {status_label}."
    if data.catatan_dosen:
        pesan += f" Catatan: {data.catatan_dosen}"

    notif = Notifikasi(
        user_id=pengajuan.mahasiswa_id,
        pesan=pesan[:255],
    )

    db.add(notif)
    db.commit()

    return {
        "message": "Status pengajuan berhasil diperbarui"
    }