import jwt
from uuid import uuid4
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from apps.auth_user.models import User, RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: int, is_manager: bool):
    expire = timezone.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "is_manager": is_manager,
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int, is_manager: bool, *, replace_token: str | None = None) -> str | None:
    """
    Создаёт новый refresh-токен для пользователя.

    Если replace_token передан, старый токен заменяется новым.
    Поддерживается максимум MAX_REFRESH_TOKENS активных токенов.
    Хэш токена хранится в БД.
    """

    tokens_qs = RefreshToken.objects.filter(user_id=user_id).order_by("created_at")

    if replace_token:

        old_token = next((t for t in tokens_qs if check_password(replace_token, t.token)), None)
        if not old_token:
            return None
        expire = old_token.expires_at
        old_token.delete()
    else:

        expire = timezone.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        max_tokens = getattr(settings, "MAX_REFRESH_TOKENS", 5)
        if tokens_qs.count() >= max_tokens:
            tokens_qs.first().delete()

    payload = {
        "user_id": user_id,
        "is_manager": is_manager,
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": str(uuid4()),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    RefreshToken.objects.create(
        user_id=user_id,
        token=make_password(token),
        expires_at=expire,
    )

    return token

def authenticate_user(username: str, password: str):
    return authenticate(username=username, password=password)

def verify_token(token: str, token_type="access"):
    """
    Проверяет JWT-токен.
    Для access-токена не трогаем БД.
    Для refresh-токена ищем хэш в БД и проверяем срок действия.
    Возвращает payload или None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != token_type:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        if token_type == "refresh":

            db_tokens = RefreshToken.objects.filter(user_id=user_id)
            db_token = next((t for t in db_tokens if check_password(token, t.token)), None)
            if not db_token:
                return None
            if db_token.expires_at <= timezone.now():
                db_token.delete()
                return None

        return payload

    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def revoke_refresh_token(token: str) -> int:
    return RefreshToken.objects.filter(token=token).delete()[0]

def revoke_all_refresh_tokens(user_id: int) -> int:
    return RefreshToken.objects.filter(user_id=user_id).delete()[0]
