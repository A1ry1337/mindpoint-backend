from datetime import date
from typing import List, Optional, Dict

from django.shortcuts import get_object_or_404
from ninja import Router, Query

from apps.auth_user.models import User
from apps.auth_user.permissions import JWTAuthManager
from apps.manager.management.models import Team
from apps.manager.management.schemas import EmployeeOut, TeamIn, AddMembersIn, TeamDass9ResultOut, TeamLeadIn, \
    TeamWithMembersOut, AssignTeamLeadIn, ManagerRequestResponseIn
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

@router.get("/get_team_members", auth=JWTAuthManager(), response=List[TeamWithMembersOut])
def get_teams_with_members(request):
    """
    Список команд
    """
    manager_id = request.auth["user_id"]
    return ManagementService.get_teams_with_members(manager_id)

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

@router.post("/assign_team_lead", auth=JWTAuthManager())
def assign_team_lead(request, data: TeamLeadIn):
    """
    Назначение роли тимлида для пользователя менеджером.
    """
    manager_id = request.auth["user_id"]
    return ManagementService.assign_team_lead(manager_id, data.user_id)

@router.post("/revoke_team_lead", auth=JWTAuthManager())
def revoke_team_lead(request, data: TeamLeadIn):
    """
    Снятие роли тимлида у пользователя менеджером.
    """
    manager_id = request.auth["user_id"]
    return ManagementService.revoke_team_lead(manager_id, data.user_id)

@router.post("/assign_team_lead_to_team", auth=JWTAuthManager())
def assign_team_lead_to_team(request, data: AssignTeamLeadIn):
    """
    Назначение команды тимлиду
    """
    manager_id = request.auth["user_id"]
    return ManagementService.assign_team_lead_to_team(manager_id, data.team_id, data.user_id)

@router.post("/revoke_team_lead_from_team", auth=JWTAuthManager())
def revoke_team_lead_from_team(request, data: AssignTeamLeadIn):
    """
    Снятие команды с тимлида
    """
    manager_id = request.auth["user_id"]
    return ManagementService.revoke_team_lead_from_team(manager_id, data.team_id, data.user_id)

@router.get("/manager_requests", auth=JWTAuthManager(), response=List[Dict])
def manager_requests(request):
    """
    Список всех pending-запросов пользователей для менеджера
    """
    manager_id = request.auth["user_id"]
    return ManagementService.list_manager_requests(manager_id)

@router.post("/respond_manager_request", auth=JWTAuthManager())
def respond_manager_request(request, data: ManagerRequestResponseIn):
    """
    Принять или отклонить запрос пользователя на закрепление за менеджером
    """
    manager_id = request.auth["user_id"]
    return ManagementService.respond_to_manager_request(manager_id, data.request_id, data.approve)

from apps.manager.management.schemas import RemoveMemberFromTeamIn, MoveMemberToAnotherTeamIn

@router.post("/remove_member_from_team", auth=JWTAuthManager())
def remove_member_from_team(request, data: RemoveMemberFromTeamIn):
    """
    Удаляет участника из команды.
    """
    manager_id = request.auth["user_id"]
    return ManagementService.remove_member_from_team(manager_id, data.team_id, data.user_id)


@router.delete("/remove_member_from_company/{user_id}", auth=JWTAuthManager())
def remove_member_from_company(request, user_id: str):
    """
    Удаляет участника из компании (открепляет от менеджера и всех команд).
    """
    manager_id = request.auth["user_id"]
    return ManagementService.remove_member_from_company(manager_id, user_id)


@router.post("/move_member_to_another_team", auth=JWTAuthManager())
def move_member_to_another_team(request, data: MoveMemberToAnotherTeamIn):
    """
    Перемещает участника из одной команды в другую.
    """
    manager_id = request.auth["user_id"]
    return ManagementService.move_member_to_another_team(
        manager_id,
        data.user_id,
        data.from_team_id,
        data.to_team_id
    )

