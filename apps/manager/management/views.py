from datetime import date
from typing import List, Optional

from django.shortcuts import get_object_or_404
from ninja import Router, Query

from apps.auth_user.models import User
from apps.auth_user.permissions import JWTAuthManager
from apps.manager.management.models import Team
from apps.manager.management.schemas import EmployeeOut, TeamIn, AddMembersIn, TeamDass9ResultOut
from apps.manager.management.services import ManagementService, Dass9TeamService

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

@router.get(
    "/dass_9_result/{team_id}",
    auth=JWTAuthManager(),
    response=TeamDass9ResultOut
)
def get_team_dass9_results(
        request,
        team_id: str,
        from_date: Optional[date] = Query(None),
        to_date: Optional[date] = Query(None),
):
    """
    Усреднённые результаты DASS-9 по выбранной команде (по дням, с возможностью фильтрации по диапазону)
    """
    manager_id = request.auth["user_id"]
    return Dass9TeamService.get_team_results(manager_id, team_id, from_date, to_date)


@router.get(
    "/dass_9_result",
    auth=JWTAuthManager(),
    response=List[TeamDass9ResultOut]
)
def get_all_teams_dass9_results(
        request,
        from_date: Optional[date] = Query(None),
        to_date: Optional[date] = Query(None),
):
    """
    Усреднённые результаты DASS-9 по всем командам руководителя (по дням, с возможностью фильтрации по диапазону)
    """
    manager_id = request.auth["user_id"]
    return Dass9TeamService.get_all_teams_results(manager_id, from_date, to_date)