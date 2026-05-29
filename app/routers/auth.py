from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.config.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.middleware.auth import create_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


@router.post("/register")
def register(data: UserCreate, db: Session = Depends(get_db)):

    allowed_roles = ["mahasiswa", "dosen", "admin"]

    if data.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail="Role tidak valid"
        )

    existing_user = db.query(User).filter(
        User.username == data.username
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username sudah dipakai"
        )

    hashed_password = hash_password(data.password)

    new_user = User(
        username=data.username,
        password=hashed_password,
        nama=data.nama,
        role=data.role.strip().lower()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "Registrasi berhasil",
        "user": UserResponse.model_validate(new_user)
    }

@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.username == data.username
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username tidak ditemukan"
        )

    if not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password salah"
        )

    token_data = {
        "id": user.id,
        "username": user.username,
        "role": user.role.strip().lower()
    }

    token = create_token(token_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "nama": user.nama,
            "role": user.role.strip().lower()
        }
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)