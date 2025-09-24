from typing import Dict, Any

from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from apps.auth_user.models import User
from apps.manager.management.models import Team


class ManagementService:
    @staticmethod
    def get_all_employees_by_manager(manager_id):
        employees = User.objects.filter(manager_id=manager_id).prefetch_related("member_teams")
        return [{
            "id": e.id,
            "username": e.username,
            "fullname": e.full_name,
            "team": {
                "id": team.id,
                "name": team.name,
            } if (team := e.member_teams.first()) else None,
        } for e in employees]

    @staticmethod
    def add_members_in_team(manager_id: str, team_id: str, user_ids: list[str]) -> Dict[str, Any]:
        """
        Добавляет нескольких участников в команду.
        """
        team = get_object_or_404(Team, id=team_id, manager_id=manager_id)

        users = User.objects.filter(
            id__in=user_ids,
            manager_id=manager_id
        )
        if not users.exists():
            raise HttpError(404, "Ни одного пользователя не найдено")

        existing_ids = set(team.members.values_list("id", flat=True))
        new_users = [u for u in users if u.id not in existing_ids]

        if not new_users:
            raise HttpError(400, "Все пользователи уже в команде")

        team.members.add(*new_users)

        return {
            "status": "members_added",
            "added_count": len(new_users),
            "skipped_count": len(users) - len(new_users),
        }

    @staticmethod
    def get_team_members(manager_id: str, team_id: str):
        team = get_object_or_404(Team, id=team_id, manager_id=manager_id)

        members = team.members.all()
        return [{
            "id": e.id,
            "username": e.username,
            "fullname": e.full_name,
        } for e in members]
