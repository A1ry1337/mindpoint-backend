from typing import Dict, Any, List, Optional

from django.db.models import Avg
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from django.utils import timezone

from apps.assessments.dass.models import Dass9Result
from apps.auth_user.models import User
from apps.employee.settings.models import ManagerAssignmentRequest
from apps.manager.management.models import Team, TeamLead
from datetime import date

class ManagementService:
    @staticmethod
    def get_all_employees_by_manager(manager_id):
        employees = User.objects.filter(manager_id=manager_id).prefetch_related("member_teams")
        return [{
            "is_teamlead": e.is_teamlead,
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
            "team": None,
            "is_teamlead": e.is_teamlead,
            "fullname": e.full_name,
        } for e in members]

    @staticmethod
    def assign_team_lead(manager_id: str, user_id: str):
        """
        Назначает роль тимлида для пользователя.
        """
        user = get_object_or_404(User, id=user_id, manager_id=manager_id)

        if user.id == manager_id:
            raise HttpError(400, "Нельзя назначить роль тимлида самому себе")

        user.is_teamlead = True
        user.save()

        return {"status": "ok", "user_id": user.id, "is_teamlead": user.is_teamlead}

    @staticmethod
    def revoke_team_lead(manager_id: str, user_id: str):
        """
        Снимает роль тимлида у пользователя.
        """
        user = get_object_or_404(User, id=user_id, manager_id=manager_id)

        if not user.is_teamlead:
            raise HttpError(400, "Пользователь не является тимлидом")

        user.is_teamlead = False
        user.save()

        return {"status": "ok", "user_id": user.id, "is_teamlead": user.is_teamlead}

    @staticmethod
    def get_teams_with_members(manager_id: str):
        teams = Team.objects.filter(manager_id=manager_id).prefetch_related("members")
        result = []
        for team in teams:
            members = [
                {
                    "id": member.id,
                    "username": member.username,
                    "fullname": member.full_name,
                    "is_teamlead": member.is_teamlead
                }
                for member in team.members.all()
            ]

            team_leads = [
                {
                    "id": l.id,
                    "username": l.username,
                    "fullname": l.full_name,
                    "is_teamlead": True
                }
                for l in team.team_leads.all()
            ]

            result.append({
                "team": {"id": team.id, "name": team.name},
                "members": members,
                "team_leads": team_leads
            })
        return result

    # назначение тимлида для команды (только для пользователей с is_teamlead=True)
    @staticmethod
    def assign_team_lead_to_team(manager_id: str, team_id: str, user_id: str):
        team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
        user = get_object_or_404(User, id=user_id)

        if not user.is_teamlead:
            raise HttpError(400, "Пользователь не является тимлидом и не может быть назначен на команду")

        TeamLead.objects.get_or_create(team=team, user=user)
        return {"status": "ok", "team_id": str(team.id), "user_id": str(user.id)}

    # отзыв тимлида с команды
    @staticmethod
    def revoke_team_lead_from_team(manager_id: str, team_id: str, user_id: str):
        team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
        user = get_object_or_404(User, id=user_id)

        deleted, _ = TeamLead.objects.filter(team=team, user=user).delete()
        if not deleted:
            raise HttpError(400, "Пользователь не является тимлидом этой команды")

        return {"status": "ok", "team_id": str(team.id), "user_id": str(user.id)}

    @staticmethod
    def list_manager_requests(manager_id: str):
        """
        Возвращает все pending-запросы пользователей, которые хотят быть закреплены за менеджером.
        """
        requests = ManagerAssignmentRequest.objects.filter(
            manager_id=manager_id,
            is_approved__isnull=True
        ).select_related("user")

        return [{
            "request_id": r.id,
            "user_id": r.user.id,
            "username": r.user.username,
            "full_name": r.user.full_name,
            "created_at": r.created_at.isoformat()
        } for r in requests]

    @staticmethod
    def respond_to_manager_request(manager_id: str, request_id: str, approve: bool):
        """
        Принять или отклонить запрос пользователя.
        """
        request_obj = get_object_or_404(
            ManagerAssignmentRequest,
            id=request_id,
            manager_id=manager_id,
            is_approved__isnull=True
        )

        request_obj.is_approved = approve
        request_obj.responded_at = timezone.now()
        request_obj.save()

        if approve:
            user = request_obj.user
            user.manager_id = manager_id
            user.save()

        return {
            "request_id": request_obj.id,
            "user_id": request_obj.user.id,
            "username": request_obj.user.username,
            "status": "approved" if approve else "rejected",
            "responded_at": request_obj.responded_at.isoformat()
        }


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