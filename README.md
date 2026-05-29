# E-Office Kampus — Backend API

Backend untuk Sistem Informasi Surat-Menyurat & Tugas Akhir.
Dibangun dengan **FastAPI (Python) + MySQL**.

---

## ⚙️ Cara Setup & Menjalankan

### 1. Prasyarat
- Python 3.10+
- MySQL (via XAMPP atau langsung)
- Git

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Buat Database MySQL

Buka MySQL Workbench atau phpMyAdmin, jalankan:

```sql
CREATE DATABASE db_eoffice;
```

> **Catatan:** Tabel akan dibuat otomatis oleh SQLAlchemy saat server pertama kali jalan.
> Kamu **tidak perlu** buat tabel manual.

### 4. Setting Environment

Edit file `.env` sesuai konfigurasi MySQL kamu

### 5. Jalankan Server

```bash
uvicorn app.main:app --reload --port 8000
```

Server berjalan di: `http://localhost:8000`
Dokumentasi API: `http://localhost:8000/docs`

---

## 📋 Daftar Endpoint API

### 🔐 Auth (`/api/auth`)
| Method | Endpoint | Akses | Keterangan |
|--------|----------|-------|------------|
| POST | `/api/auth/register` | Public | Daftar akun baru |
| POST | `/api/auth/login` | Public | Login, dapat token JWT |
| GET | `/api/auth/me` | Semua (login) | Cek data user aktif |

### 📄 Pengajuan (`/api/pengajuan`)
| Method | Endpoint | Akses | Keterangan |
|--------|----------|-------|------------|
| POST | `/api/pengajuan/` | Mahasiswa | Buat pengajuan baru + upload file |
| GET | `/api/pengajuan/saya` | Mahasiswa | Lihat riwayat pengajuan sendiri |
| DELETE | `/api/pengajuan/{id}` | Mahasiswa | Hapus pengajuan (hanya pending) |
| GET | `/api/pengajuan/semua` | Dosen, Admin | Lihat semua pengajuan + nama mahasiswa |
| PUT | `/api/pengajuan/{id}` | Dosen | Setujui atau tolak pengajuan |
| GET | `/api/pengajuan/download/{filename}` | Semua (login) | Download file berkas |

### 🔔 Notifikasi (`/api/notifikasi`)
| Method | Endpoint | Akses | Keterangan |
|--------|----------|-------|------------|
| GET | `/api/notifikasi/` | Semua (login) | Lihat semua notifikasi |
| GET | `/api/notifikasi/belum-dibaca` | Semua (login) | Jumlah notif belum dibaca (badge FE) |
| PUT | `/api/notifikasi/baca-semua` | Semua (login) | Tandai semua sudah dibaca |

### 👤 Admin (`/api/admin`)
| Method | Endpoint | Akses | Keterangan |
|--------|----------|-------|------------|
| GET | `/api/admin/dashboard` | Admin | Card stats untuk dashboard |
| GET | `/api/admin/users` | Admin | Daftar semua user |
| POST | `/api/admin/users` | Admin | Tambah user baru |
| DELETE | `/api/admin/users/{id}` | Admin | Hapus akun user |

---

## 🔑 Cara Kirim Token ke API (untuk FE)

Setelah login, simpan `access_token` dari response.
Kirim di setiap request yang butuh login:

```
Header:
Authorization: Bearer <token_disini>
```

Contoh di Axios (React):
```js
axios.get('/api/pengajuan/saya', {
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`
  }
})
```

---

## 📁 Struktur Folder

```
e_office_backend/
├── app/
│   ├── main.py           ← Entry point, CORS, register router
│   ├── config/
│   │   └── database.py   ← Koneksi MySQL
│   ├── models/           ← Definisi tabel database (SQLAlchemy)
│   │   ├── user.py
│   │   ├── pengajuan.py
│   │   └── notifikasi.py
│   ├── schemas/          ← Validasi input/output (Pydantic)
│   │   ├── user.py
│   │   └── pengajuan.py
│   ├── routers/          ← Semua endpoint API
│   │   ├── auth.py
│   │   ├── pengajuan.py
│   │   ├── notifikasi.py
│   │   └── admin.py
│   └── middleware/
│       └── auth.py       ← JWT verify, require_role
├── uploads/              ← File PDF yang diupload mahasiswa
├── .env                  ← Konfigurasi (JANGAN di-push ke GitHub!)
├── requirements.txt
└── README.md
```

---

## ❗ Troubleshooting

**Error `Access-Control-Allow-Origin`** → Pastikan URL frontend ada di list `origins` di `app/main.py`

**Error koneksi database** → Cek isi `.env`, pastikan XAMPP MySQL sudah nyala

**`ModuleNotFoundError`** → Jalankan `pip install -r requirements.txt` ulang

**Token expired** → Login ulang untuk dapat token baru (token berlaku 8 jam)
