# E-Office Backend

Panduan singkat menjalankan backend FastAPI (Python).

Prasyarat

- Python 3.11+ (disarankan)
- pip
- MySQL atau gunakan konfigurasi database yang ada di `app/config/database.py`

Instalasi & jalankan (Windows PowerShell)

1. Buat virtualenv dan aktifkan:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependensi:
   ```powershell
   pip install -r requirements.txt
   ```
3. Siapkan file environment (contoh `.env`) jika diperlukan (lihat `app/config/database.py` untuk variabel yang dibaca).
4. Jalankan server (port default 8000):
   ```powershell
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

Catatan penting

- Semua router di-include dengan prefix `/api`. Endpoint umum:
  - POST /api/auth/register
  - POST /api/auth/login
  - GET /api/auth/me
  - POST /api/mahasiswa/pengajuan
  - GET /api/mahasiswa/pengajuan/me
  - GET /api/dosen/pengajuan
  - ... (lihat folder `app/routers`)

- Pastikan CORS middleware mengizinkan origin frontend (mis. http://localhost:5173). Jika ada error CORS, cek `app/main.py` dan urutan middleware/routers.

Troubleshooting cepat

- 404 Not Found: cek apakah server sudah berjalan di `127.0.0.1:8000` dan prefix `/api` aktif.
- 422 Unprocessable Entity saat submit FormData: pastikan field nama cocok dengan parameter di router dan header tidak memaksa `Content-Type: application/json` ketika mengirim FormData (frontend harus mengirim FormData tanpa override header).
- 403 Forbidden: biasanya role/token tidak sesuai. Pastikan token JWT valid dan user memiliki role yang benar.
- 500 Internal Server Error: lihat log server di terminal untuk traceback.

Database

- Schema dibuat otomatis pada startup (`Base.metadata.create_all`) — cek `app/main.py`.
- Untuk produksi gunakan migrasi (alembic) — belum disertakan di project ini.

Debug & development

- Gunakan `--reload` saat pengembangan.
- Pastikan file `uploads/` ada dan writable untuk upload.

Kontak

- Dokumentasi endpoint ada di http://127.0.0.1:8000/docs setelah server dijalankan.
