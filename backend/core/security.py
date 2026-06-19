import bcrypt
from itsdangerous import URLSafeTimedSerializer
from .config import settings

# Хеширование пароля
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# Сессии (подписанные куки)
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

def create_session_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})

def decode_session_token(token: str) -> dict:
    try:
        return serializer.loads(token, max_age=settings.SESSION_MAX_AGE)
    except Exception:
        return None
    

# Добавьте в конец файла backend/core/security.py
from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from ..core.database import SessionLocal
from ..models.user import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("tempa_session")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_session_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid session")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user