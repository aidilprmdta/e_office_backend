from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "rahasia")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

security = HTTPBearer()


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sudah kadaluarsa, silakan login ulang",
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid",
        )

def get_current_user(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user_id = token.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token tidak mengandung data user")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    return user


def require_role(*roles):
    def checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.strip().lower()
        allowed_roles = [r.strip().lower() for r in roles]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' tidak memiliki akses. Hanya untuk: {', '.join(allowed_roles)}",
            )
        return current_user
    return checker
