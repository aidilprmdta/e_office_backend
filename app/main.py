from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="E-Office Kampus API",
    description="Sistem Informasi Surat-Menyurat & Tugas Akhir", [cite: 1]
    version="1.0.0"
)

# Konfigurasi CORS (PENTING untuk Anak FE) 
origins = [
    "http://localhost:5173", # URL default Vite + React
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Mengizinkan GET, POST, PUT, DELETE 
    allow_headers=["*"],
)

# Endpoint Testing awal
@app.get("/")
def read_root():
    return {"message": "Server FastAPI E-Office Berhasil Berjalan!"}

# Nanti Router dari folder app/routers/ tinggal di-import dan di-register di sini:
# from app.routers import auth, pengajuan
# app.include_router(auth.router)