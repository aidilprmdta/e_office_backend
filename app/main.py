from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config.database import engine
from app.models import user, pengajuan, notifikasi
from app.routers import auth, dosen, mahasiswa, admin, notifikasi as notifikasi_router
from app.routers import search, verifikasi


# =====================================================
# CREATE DATABASE TABLES
# =====================================================
user.Base.metadata.create_all(bind=engine)
pengajuan.Base.metadata.create_all(bind=engine)
notifikasi.Base.metadata.create_all(bind=engine)


# =====================================================
# FASTAPI APP
# =====================================================
app = FastAPI(
    title="E-Office Kampus API",
    description="Sistem Informasi Surat-Menyurat & Tugas Akhir",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# =====================================================
# CORS
# =====================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# STATIC FILES
# =====================================================
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# =====================================================
# ROUTERS
# =====================================================
app.include_router(auth.router)
app.include_router(mahasiswa.router)
app.include_router(dosen.router)
app.include_router(admin.router)
app.include_router(notifikasi_router.router)
app.include_router(search.router)
app.include_router(verifikasi.router)


# =====================================================
# ROOT
# =====================================================
@app.get("/")
def read_root():
    return {
        "message": "Server FastAPI E-Office Berhasil Berjalan!",
        "docs": "/docs"
    }
