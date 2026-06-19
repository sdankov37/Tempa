import tempfile
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./tempa.db"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    SESSION_COOKIE_NAME: str = "tempa_session"
    SESSION_MAX_AGE: int = 86400
    REDIS_URL: str = "redis://localhost:6379/0"
    MAX_FILE_SIZE: int = 2 * 1024 * 1024 * 1024
    TEMP_DIR: str = tempfile.gettempdir()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()