from django.db.models import Q
from ninja import Router
from django.contrib.auth import get_user_model
from ninja.responses import Response
from django.conf import settings

from apps.auth_user.permissions import JWTAuth
from apps.auth_user.schemas import UserCreateSchema, LoginResponse
from apps.auth_user.services import create_access_token, create_refresh_token, authenticate_user, verify_token, \
    REFRESH_TOKEN_EXPIRE_DAYS
from ninja.errors import HttpError

User = get_user_model()
router = Router()

@router.post("/register", response=dict)
def register(request, data: UserCreateSchema):
    user = User.objects.filter(
        Q(username=data.username) |
        (Q(email=data.email) & ~Q(email__isnull=True) & ~Q(email=""))
    ).first()
    if user:
        raise HttpError(400, "Пользователь с таким никнеймом или почтой уже существует")
    User.objects.create_user(
        manager= User.objects.filter(id=data.managerId).first(),
        email=data.email or "",
        username=data.username,
        password=data.password,
        full_name=data.full_name or ""
    )
    return {"message": "Пользователь успешно зарегистрирован"}

@router.post("/login", response=LoginResponse)
def login(request, data: UserCreateSchema):
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")

    access = create_access_token(user.id.int)
    refresh = create_refresh_token(user.id.int)

    response = Response({
        "access": access,
        "userId": user.id,
        "username": user.__str__(),
        "fullname": user.full_name,
        "isManager": user.is_manager,
    })

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )
    return response

@router.get("/refresh")
def refresh_token(request):
    refresh_token_from_cookies = request.COOKIES.get("refresh_token")
    if not refresh_token_from_cookies:
        raise HttpError(401, "No refresh token")

    payload = verify_token(refresh_token_from_cookies, token_type="refresh")
    if not payload:
        raise HttpError(401, "Invalid refresh token")

    access = create_access_token(payload['user_id'])
    new_refresh = create_refresh_token(payload['user_id'], replace_token=refresh_token_from_cookies)

    response = Response({"access": access})
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Strict",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return response


@router.get("/hello", auth=JWTAuth())
def hello(request):
    user = User.objects.filter(id=request.auth["user_id"]).first()
    return {
        "message": f"Hello, {user}!",
        "СОТРУДНИКИ": f"Hello, {[employee.username for employee in user.employees.all()]}!"
    }

