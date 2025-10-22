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
router = Router(tags=["Authentication(Аутентификация)"])

@router.post("/register", response=dict)
def register(request, data: UserCreateSchema):
    """
    Регистрирует нового пользователя.

    - Проверяет уникальность username и email (если указан).
    - Создаёт пользователя с указанными данными.
    - Если указан is_manager = true то пользователю выдается роль менеджера.
    """
    user = User.objects.filter(
        Q(username=data.username) |
        (Q(email=data.email) & ~Q(email__isnull=True) & ~Q(email=""))
    ).first()
    if user:
        raise HttpError(400, "Пользователь с таким никнеймом или почтой уже существует")
    User.objects.create_user(
        email=data.email or "",
        username=data.username,
        password=data.password,
        full_name=data.full_name or "",
        is_manager=data.is_manager or False
    )
    return {"message": "Пользователь успешно зарегистрирован"}

@router.post("/login", response=LoginResponse)
def login(request, data: UserCreateSchema):
    """
    Аутентификация пользователя.

    - Принимает username и password.
    - Если данные корректные, генерирует `access` и `refresh` токены.
    - `refresh_token` записывается в куки.

    **Возвращает:**
    Объект с полями:
    - `access` — JWT для авторизации запросов.
    - `userId` — UUID пользователя.
    - `username` — никнейм.
    - `fullname` — полное имя.
    - `is_manager` — флаг, является ли пользователь руководителем.
    """
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")

    access = create_access_token(user.id.int, user.is_manager)
    refresh = create_refresh_token(user.id.int, user.is_manager)

    response = Response({
        "access": access,
        "userId": user.id,
        "username": user.__str__(),
        "fullname": user.full_name,
        "is_manager": user.is_manager,
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
    """
    Обновление access-токена по refresh-токену.

    - Читает refresh_token из cookies.
    - Проверяет его валидность.
    - Возвращает новый access-токен и обновляет refresh-токен в cookies.
    """
    refresh_token_from_cookies = request.COOKIES.get("refresh_token")
    if not refresh_token_from_cookies:
        raise HttpError(401, "No refresh token")

    payload = verify_token(refresh_token_from_cookies, token_type="refresh")
    if not payload:
        raise HttpError(401, "Invalid refresh token")

    access = create_access_token(payload['user_id'], payload['is_manager'])
    new_refresh = create_refresh_token(payload['user_id'], payload['is_manager'], replace_token=refresh_token_from_cookies)

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
    """
    Тест запрос
    """
    user = User.objects.filter(id=request.auth["user_id"]).first()
    return {
        "message": f"Hello, {user}!",
        "СОТРУДНИКИ": f"Hello, {[employee.username for employee in user.employees.all()]}!"
    }

