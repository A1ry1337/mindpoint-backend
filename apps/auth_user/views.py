from ninja import Router
from django.contrib.auth import get_user_model

from apps.auth_user.permissions import JWTAuth
from apps.auth_user.schemas import UserCreateSchema, UserReadSchema, TokenSchema, TokenRefreshSchema
from apps.auth_user.services import create_access_token, create_refresh_token, authenticate_user, verify_token
from ninja.errors import HttpError

User = get_user_model()
router = Router()

@router.post("/register", response=dict)
def register(request, data: UserCreateSchema):
    user = User.objects.filter(email=data.email).first()
    if user:
        raise HttpError(400, "Пользователь с данной почтой уже существует")
    user = User.objects.create_user(
        email=data.email or "",
        username=data.username,
        password=data.password,
        full_name=data.full_name or ""
    )
    return {"message": "Пользователь успешно зарегистрирован"}

@router.post("/login", response=TokenSchema)
def login(request, data: UserCreateSchema):
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")
    access = create_access_token(user.id.int)
    refresh = create_refresh_token(user.id.int)
    return {"access": access, "refresh": refresh}

@router.post("/refresh", response=TokenSchema)
def refresh_token(request, data: TokenRefreshSchema):
    user = verify_token(data.refresh, token_type="refresh")
    if not user:
        raise HttpError(401, "Invalid refresh token")
    access = create_access_token(user.id.int)
    refresh = create_refresh_token(user.id.int, replace_token=data.refresh)
    return {"access": access, "refresh": refresh}

@router.get("/hello", auth=JWTAuth())
def hello(request):
    user = request.auth
    return {"message": f"Hello, {user.username}!"}
