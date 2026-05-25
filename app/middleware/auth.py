from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "rahasia")
ALGORITHM = "HS256"
# Token berlaku 8 jam
ACCESS_TOKEN_EXPIRE_HOURS = 8

security = HTTPBearer()

def create_token(data: dict):
    """Buat JWT token dengan waktu kadaluarsa 8 jam"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verifikasi dan decode JWT token dari header Authorization"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kadaluarsa, silakan login ulang"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid"
        )

def get_current_user(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    """Ambil data user dari database berdasarkan id di dalam token"""
    user_id = token.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token tidak mengandung data user")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    return user

def require_role(*roles):
    """
    Dependency factory untuk membatasi akses berdasarkan role.
    Contoh pemakaian: Depends(require_role("dosen", "admin"))
    """
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Halaman ini hanya untuk: {', '.join(roles)}"
            )
        return current_user
    return checker
