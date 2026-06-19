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