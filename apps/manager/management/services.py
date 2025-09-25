from typing import Dict, Any, List, Optional

from django.db.models import Avg
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError

from apps.assessments.dass.models import Dass9Result
from apps.auth_user.models import User
from apps.manager.management.models import Team
from datetime import date

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

class Dass9TeamService:

    @staticmethod
    def _filter_by_date(qs, from_date: Optional[date], to_date: Optional[date]):
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)
        return qs

    @staticmethod
    def get_team_results(manager_id: str, team_id: str,
                         from_date: Optional[date] = None,
                         to_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Средние результаты DASS-9 по команде (группировка по датам, с фильтрацией по диапазону)
        """
        team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
        member_ids = team.members.values_list("id", flat=True)

        qs = Dass9Result.objects.filter(user_id__in=member_ids)
        qs = Dass9TeamService._filter_by_date(qs, from_date, to_date)

        results = (
            qs.values("date")
            .annotate(
                depression_avg=Avg("depression_score"),
                stress_avg=Avg("stress_score"),
                anxiety_avg=Avg("anxiety_score"),
            )
            .order_by("date")
        )

        return {
            "team": team.name,
            "results": list(results)
        }

    @staticmethod
    def get_all_teams_results(manager_id: str,
                              from_date: Optional[date] = None,
                              to_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Средние результаты DASS-9 по всем командам + дефолтная команда (по дням, с фильтрацией)
        """
        response = []
        teams = Team.objects.filter(manager_id=manager_id)

        for team in teams:
            member_ids = team.members.values_list("id", flat=True)
            qs = Dass9Result.objects.filter(user_id__in=member_ids)
            qs = Dass9TeamService._filter_by_date(qs, from_date, to_date)

            results = (
                qs.values("date")
                .annotate(
                    depression_avg=Avg("depression_score"),
                    stress_avg=Avg("stress_score"),
                    anxiety_avg=Avg("anxiety_score"),
                )
                .order_by("date")
            )
            response.append({"team": team.name, "results": list(results)})

        # пользователи без команды
        members_without_team = User.objects.filter(member_teams=None).exclude(id=manager_id)
        if members_without_team.exists():
            member_ids = members_without_team.values_list("id", flat=True)
            qs = Dass9Result.objects.filter(user_id__in=member_ids)
            qs = Dass9TeamService._filter_by_date(qs, from_date, to_date)

            results = (
                qs.values("date")
                .annotate(
                    depression_avg=Avg("depression_score"),
                    stress_avg=Avg("stress_score"),
                    anxiety_avg=Avg("anxiety_score"),
                )
                .order_by("date")
            )
            response.append({"team": "unknown", "results": list(results)})

        return response