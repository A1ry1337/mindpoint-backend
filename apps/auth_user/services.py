import jwt
from datetime import datetime, timedelta
from django.conf import settings
from apps.auth_user.models import User
from django.contrib.auth import authenticate

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: int):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"user_id": user_id, "exp": expire, "type": "access"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def create_refresh_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"user_id": user_id, "exp": expire, "type": "refresh"}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def authenticate_user(username: str, password: str):
    user = authenticate(username=username, password=password)
    return user

def verify_token(token: str, token_type="access"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        user_id = payload.get("user_id")
        user = User.objects.filter(id=user_id).first()
        return user
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
