from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.database import engine
from app.models import user, pengajuan, notifikasi
from app.routers import auth, pengajuan as pengajuan_router, notifikasi as notifikasi_router, admin
import os

# Buat semua tabel otomatis di database (jika belum ada)
user.Base.metadata.create_all(bind=engine)
pengajuan.Base.metadata.create_all(bind=engine)
notifikasi.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Office Kampus API",
    description="Sistem Informasi Surat-Menyurat & Tugas Akhir",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI: buka http://localhost:8000/docs
    redoc_url="/redoc"
)

# ─── CORS (WAJIB agar FE React tidak error Cross-Origin) ──────
origins = [
    "http://localhost:5173",   # Vite default
    "http://127.0.0.1:5173",
    "http://localhost:3000",   # CRA fallback
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files untuk akses file upload via URL ─────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ─── Register semua router ────────────────────────────────────
app.include_router(auth.router)
app.include_router(pengajuan_router.router)
app.include_router(notifikasi_router.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {
        "message": "Server FastAPI E-Office Berhasil Berjalan!",
        "docs": "Buka /docs untuk dokumentasi API lengkap"
    }
