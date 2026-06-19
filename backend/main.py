from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core.database import Base, engine
from backend.api import auth_router
from backend.api.tasks import router as tasks_router
from backend.core.security import decode_session_token
import os

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tempa API",
    version="1.0",
    swagger_ui_parameters={"withCredentials": True}
)

# CORS
origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:5500",   # ← добавьте это
    "http://127.0.0.1:5500",
    "null",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(auth_router)

# Статика (фронтенд)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/")
async def root():
    return FileResponse(os.path.join(frontend_path, "index.html"))

# Middleware авторизации
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Публичные пути
    public_paths = [
        "/auth", "/docs", "/openapi.json", "/frontend",
        "/", "/script.js", "/style.css", "/favicon.ico", "/health"
    ]
    if any(request.url.path.startswith(p) or request.url.path == p for p in public_paths):
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