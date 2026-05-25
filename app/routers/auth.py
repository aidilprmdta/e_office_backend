from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.middleware.auth import create_token, get_current_user
from passlib.context import CryptContext

router = APIRouter(prefix="/api/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """
    Daftarkan akun baru.
    - Role harus salah satu dari: mahasiswa, dosen, admin
    - Username harus unik (NIM untuk mahasiswa, NIDN untuk dosen)
    """
    allowed_roles = ["mahasiswa", "dosen", "admin"]
    if data.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Role tidak valid. Pilih salah satu: {', '.join(allowed_roles)}"
        )

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username sudah dipakai")

    hashed = hash_password(data.password)
    user = User(
        username=data.username,
        password=hashed,
        nama=data.nama,
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {
        "message": "Registrasi berhasil",
        "user": UserResponse.model_validate(user)
    }

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Login dan dapatkan JWT token.
    Token berlaku 8 jam. Kirim token ini di header setiap request:
    Authorization: Bearer <token>
    """
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah"
        )

    token = create_token({"id": user.id, "username": user.username, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "nama": user.nama,
        "id": user.id
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Cek siapa user yang sedang login berdasarkan token (berguna untuk FE)"""
    return UserResponse.model_validate(current_user)
