from typing import List

from django.shortcuts import get_object_or_404
from ninja import Router

from apps.auth_user.models import User
from apps.auth_user.permissions import JWTAuthManager
from apps.manager.management.models import Team
from apps.manager.management.schemas import EmployeeOut, TeamIn, AddMembersIn
from apps.manager.management.services import ManagementService

router = Router(tags=["Management(Управление персоналом)"])

@router.get("/get_all_employees", auth=JWTAuthManager(), response=List[EmployeeOut])
def get_all_employees(request):
    """
    Возвращает список всех сотрудников, закреплённых за руководителем.
    Идентификатор руководителя определяется из JWT-токена, переданного в заголовках запроса.
    """

    user_id = request.auth["user_id"]

    employees = ManagementService.get_all_employees_by_manager(user_id)

    return employees

@router.post("/create_team", auth=JWTAuthManager())
def create_team(request, data: TeamIn):
    """
    Создание команды
    """
    manager_id = request.auth["user_id"]
    manager = get_object_or_404(User, id=manager_id)

    Team.objects.create(name=data.name, manager=manager)
    return {"status": "ok"}

@router.delete("/delete_team/{team_id}", auth=JWTAuthManager())
def delete_team(request, team_id: str):
    """
    Удаляет команду по ID, если руководитель совпадает с авторизованным пользователем.
    """
    manager_id = request.auth["user_id"]
    team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
    team.delete()
    return {"status": "deleted"}

@router.post("/add_members_in_team", auth=JWTAuthManager())
def add_members_to_team(request, data: AddMembersIn):
    """
    Добавляет сразу нескольких участников в команду.
    """
    manager_id = request.auth["user_id"]
    return ManagementService.add_members_in_team(manager_id, data.team_id, data.user_ids)

@router.get("/get_team_members/{team_id}", auth=JWTAuthManager(), response=List[EmployeeOut])
def get_team_members(request, team_id: str):
    """
    Возвращает всех участников команды по ID.
    Доступно только руководителю этой команды.
    """
    manager_id = request.auth["user_id"]
    return ManagementService.get_team_members(manager_id, team_id)
