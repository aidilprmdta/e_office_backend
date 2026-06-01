# Perbaikan Virtual Environment (JWT)

Jika login/register berhasil tetapi dashboard/API lain error `ExpiredSignatureError` atau `module 'jwt' has no attribute`:

1. Pakai **venv di folder ini** (`e_office_backend\env`), bukan venv di folder lain.
2. Hapus paket JWT salah dan pasang PyJWT:

```powershell
cd e_office_backend
.\env\Scripts\python.exe -m pip uninstall jwt -y
Remove-Item -Recurse -Force .\env\Lib\site-packages\jwt -ErrorAction SilentlyContinue
.\env\Scripts\python.exe -m pip install PyJWT==2.8.0
```

3. Jalankan server dengan Python venv yang sama:

```powershell
.\env\Scripts\uvicorn.exe app.main:app --reload --port 8000
```
