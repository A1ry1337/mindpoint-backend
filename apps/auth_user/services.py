import jwt
from uuid import uuid4
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from apps.auth_user.models import User, RefreshToken
from django.contrib.auth import authenticate

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: int):
    expire = timezone.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "user_id": user_id,
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: int, *, replace_token: str | None = None):

    if replace_token:
        old_token = RefreshToken.objects.filter(user_id=user_id, token=replace_token).first()
        if not old_token:
            return None
        expire = old_token.expires_at
        old_token.delete()
    else:
        expire = timezone.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        tokens_qs = RefreshToken.objects.filter(user_id=user_id).order_by("created_at")
        if tokens_qs.count() >= getattr(settings, "MAX_REFRESH_TOKENS", 5):
            oldest = tokens_qs.first()
            oldest.delete()

    payload = {
        "user_id": user_id,
        "exp": int(expire.timestamp()),
        "type": "refresh",
        "jti": str(uuid4()),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    RefreshToken.objects.create(
        user_id=user_id,
        token=token,
        expires_at=expire,
    )
    return token

def authenticate_user(username: str, password: str):
    return authenticate(username=username, password=password)

def verify_token(token: str, token_type="access"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        user_id = payload.get("user_id")

        if token_type == "refresh":
            db_token = RefreshToken.objects.filter(user_id=user_id, token=token).first()
            if not db_token:
                return None
            if db_token.expires_at <= timezone.now():
                db_token.delete()
                return None

        user = User.objects.filter(id=user_id, is_active=True).first()
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def revoke_refresh_token(token: str) -> int:
    return RefreshToken.objects.filter(token=token).delete()[0]

def revoke_all_refresh_tokens(user_id: int) -> int:
    return RefreshToken.objects.filter(user_id=user_id).delete()[0]
