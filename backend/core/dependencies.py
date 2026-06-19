from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from ..models.user import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    # Берём user_id из состояния, установленного middleware
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        # Если middleware не сработал (например, из-за ошибки), возвращаем 401
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user