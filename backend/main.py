from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.core.database import Base, engine, SessionLocal
from backend.api import auth_router
from backend.core.security import decode_session_token
from backend.models.user import User
from backend.api.tasks import router as tasks_router

# Создаём таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Tempa API", version="1.0")

# CORS (для локальной разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(tasks_router)
app.include_router(auth_router)

# Middleware для проверки аутентификации (кроме /auth/* и /health)
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/auth") or request.url.path == "/health":
        return await call_next(request)
    
    token = request.cookies.get("tempa_session")
    if not token:
        return Response("Not authenticated", status_code=401)
    payload = decode_session_token(token)
    if not payload:
        return Response("Invalid session", status_code=401)
    request.state.user_id = payload["user_id"]
    return await call_next(request)

@app.get("/health")
def health():
    return {"status": "ok"}

# Вспомогательная зависимость для получения текущего пользователя
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

