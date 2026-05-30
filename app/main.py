from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from app.config.database import engine
from app.config.migrate import run_migrations

from app.models import user, pengajuan, notifikasi, pengajuan_status_log
import os
from app.routers import auth
from app.routers import dosen
from app.routers import mahasiswa
from app.routers import admin
from app.routers import admin_pengajuan
from app.routers import notifikasi as notifikasi_router
from app.routers import search
from app.routers import verifikasi


user.Base.metadata.create_all(bind=engine)
pengajuan.Base.metadata.create_all(bind=engine)
pengajuan_status_log.Base.metadata.create_all(bind=engine)
notifikasi.Base.metadata.create_all(bind=engine)
run_migrations()


app = FastAPI(
    title="E-Office Kampus API",
    description="Sistem Informasi Surat-Menyurat & Tugas Akhir",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def handle_options_preflight(request: Request, call_next):
    """Pastikan preflight OPTIONS tidak gagal sebelum auth middleware."""
    if request.method == "OPTIONS":
        origin = request.headers.get("origin", "*")
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "86400",
            },
        )
    return await call_next(request)

os.makedirs("uploads", exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

app.include_router(auth.router)

app.include_router(mahasiswa.router)

app.include_router(dosen.router)

app.include_router(admin.router)

app.include_router(admin_pengajuan.router)

app.include_router(notifikasi_router.router)

app.include_router(search.router)

app.include_router(verifikasi.router)


@app.get("/")
def read_root():

    return {
        "message": "Server FastAPI E-Office Berhasil Berjalan!",
        "docs": "/docs"
    }
