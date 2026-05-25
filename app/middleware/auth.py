from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.models.user import User
import jwt
import os
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "rahasia")
ALGORITHM = "HS256"

security = HTTPBearer()

def create_token(data: dict):
    return jwt.encode(data, JWT_SECRET, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

def get_current_user(token: dict = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == token.get("id")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")
    return user

def require_role(*roles):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Akses ditolak")
        return current_user
    return checker
