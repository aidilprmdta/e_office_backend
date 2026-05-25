from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.database import engine
from app.models import user, pengajuan, notifikasi
from app.routers import auth, pengajuan as pengajuan_router, notifikasi as notifikasi_router, admin

# Buat semua tabel otomatis di database
user.Base.metadata.create_all(bind=engine)
pengajuan.Base.metadata.create_all(bind=engine)
notifikasi.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="E-Office Kampus API",
    description="Sistem Informasi Surat-Menyurat & Tugas Akhir",
    version="1.0.0"
)

# Konfigurasi CORS (PENTING untuk Anak FE)
origins = [
    "http://localhost:5173",  # URL default Vite + React
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register semua router
app.include_router(auth.router)
app.include_router(pengajuan_router.router)
app.include_router(notifikasi_router.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Server FastAPI E-Office Berhasil Berjalan!"}
