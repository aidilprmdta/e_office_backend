from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config.database import engine

from app.models import user
from app.models import pengajuan
from app.models import notifikasi

from app.routers import auth
from app.routers import mahasiswa
from app.routers import dosen
from app.routers import admin
from app.routers import notifikasi as notifikasi_router

import os
from app.routers import mahasiswa


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
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# STATIC FILES
# =====================================================
os.makedirs("uploads", exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)


# =====================================================
# ROUTERS
# =====================================================
app.include_router(auth.router)

app.include_router(mahasiswa.router)

app.include_router(dosen.router)

app.include_router(admin.router)
app.include_router(mahasiswa.router)

app.include_router(notifikasi_router.router)


# =====================================================
# ROOT
# =====================================================
@app.get("/")
def read_root():

    return {
        "message": "Server FastAPI E-Office Berhasil Berjalan!",
        "docs": "/docs"
    }