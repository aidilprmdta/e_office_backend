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

    return db.query(Pengajuan).all()


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

    pengajuan.status = data.status
    pengajuan.catatan_dosen = data.catatan_dosen

    db.commit()

    notif = Notifikasi(
        user_id=pengajuan.mahasiswa_id,
        pesan=f"Pengajuan {pengajuan.status}"
    )

    db.add(notif)
    db.commit()

    return {
        "message": "Status pengajuan berhasil diperbarui"
    }