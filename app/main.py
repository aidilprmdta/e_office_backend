from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.database import engine
from app.models import user, pengajuan, notifikasi
from app.routers import auth, pengajuan as pengajuan_router, notifikasi as notifikasi_router, admin
import os
from app.routers import mahasiswa

user.Base.metadata.create_all(bind=engine)
pengajuan.Base.metadata.create_all(bind=engine)
notifikasi.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Office Kampus API",
    description="Sistem Informasi Surat-Menyurat & Tugas Akhir",
    version="1.0.0",
    docs_url="/docs",       
    redoc_url="/redoc"
)

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

os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router)
app.include_router(pengajuan_router.router)
app.include_router(notifikasi_router.router)
app.include_router(admin.router)
app.include_router(mahasiswa.router)

@app.get("/")
def read_root():
    return {
        "message": "Server FastAPI E-Office Berhasil Berjalan!",
        "docs": "Buka /docs untuk dokumentasi API lengkap"
    }
