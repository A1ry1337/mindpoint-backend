from datetime import date, timedelta
from typing import List, Optional, Dict
from uuid import UUID
from collections import Counter

from django.utils import timezone

from apps.assessments.mood.models import MoodResult
from apps.manager.management.models import Team


class MoodStatisticsService:

    @staticmethod
    def get_teams_mood(
        is_manager: bool,
        user_id: str,
        manager_id: str,
        period: str,
        team_id: Optional[UUID] = None
    ) -> Dict:
        """
        Возвращает для каждой команды статистику настроения (1–5)
        разбитую на периоды:
          - week  -> 7 дней (по дням)
          - month -> 4 недели (текущая + 3 предыдущие)
          - year  -> 12 месяцев (по месяцам)
        """
        period = (period or "week").lower()
        today = timezone.now().date()

        if period == "week":
            ranges = MoodStatisticsService._get_week_day_ranges(today)
        elif period == "month":
            ranges = MoodStatisticsService._get_month_week_ranges(today)
        elif period == "year":
            ranges = MoodStatisticsService._get_year_month_ranges(today)
        else:
            ranges = MoodStatisticsService._get_week_day_ranges(today)

        teams_qs = Team.objects.filter(manager_id=manager_id)
        if team_id:
            teams_qs = teams_qs.filter(id=team_id)
        if not is_manager:
            teams_qs = teams_qs.filter(team_leads__id=user_id)

        result_items = []

        for team in teams_qs:
            team_points = []

            for start_date, end_date, label in ranges:
                members = team.members.all()

                mood_qs = (
                    MoodResult.objects
                    .filter(user__in=members, date__gte=start_date, date__lte=end_date)
                    .values("score")
                    .annotate(count=__import__("django.db.models", fromlist=["Count"]).Count("id"))
                    .order_by("score")
                )

                score_map = {row["score"]: row["count"] for row in mood_qs}
                total_responses = sum(score_map.values())

                point_data = {
                    "period_label": label,
                    "start_date": start_date,
                    "end_date": end_date,
                    "total_responses": total_responses,
                }

                if total_responses > 0:
                    point_data["scores"] = [
                        {"score": s, "count": score_map.get(s, 0)}
                        for s in range(1, 6)
                    ]

                team_points.append(point_data)

            rec_trigger = False
            for i in range(len(team_points) - 1):
                prev = team_points[i]
                curr = team_points[i + 1]
                if not prev.get("scores") or not curr.get("scores"):
                    continue
                prev_total = prev["total_responses"]
                curr_total = curr["total_responses"]
                prev_avg = sum(x["score"] * x["count"] for x in prev["scores"]) / prev_total if prev_total else 0
                curr_avg = sum(x["score"] * x["count"] for x in curr["scores"]) / curr_total if curr_total else 0
                if 4 <= prev_avg <= 5 and 1 <= curr_avg <= 3:
                    rec_trigger = True
                    break

            result_items.append({
                "team_id": team.id,
                "team_name": team.name,
                "recommendation_trigger": rec_trigger,
                "points": team_points,
            })

        return {"items": result_items}


    PERIOD_TO_DAYS = {
        "week": 7,
        "month": 31,
        "year": 365,
    }

    @staticmethod
    def get_mood_distribution(
        is_manager: bool,
        manager_id: str,
        user_id: str,
        period: str,
        team_ids: Optional[List[UUID]] = None,
    ) -> Dict:
        """
        Возвращает количество прохождений и процентное распределение
        оценок настроения (1–5) по всем участникам указанных команд
        за выбранный период.

        period:
          week  → последние 7 дней
          month → последние 31 день
          year  → последние 365 дней

        rec_mood_trigger = True, если 60%+ прохождений имели оценку 1 или 2.
        """
        days = MoodStatisticsService.PERIOD_TO_DAYS.get(period, 7)

        today = timezone.now().date()
        start_date = today - timedelta(days=days - 1)

        # Определяем команды
        teams_qs = Team.objects.filter(manager_id=manager_id)
        if team_ids:
            teams_qs = teams_qs.filter(id__in=team_ids)
        if not is_manager:
            teams_qs = teams_qs.filter(team_leads__id=user_id)

        # Участники всех найденных команд (без дублей)
        member_ids = (
            Team.objects
            .filter(id__in=teams_qs.values_list("id", flat=True))
            .values_list("members", flat=True)
            .distinct()
        )

        # Все прохождения за период — каждая запись = одно прохождение
        scores = list(
            MoodResult.objects
            .filter(user__in=member_ids, date__gte=start_date, date__lte=today)
            .values_list("score", flat=True)
        )

        total_completions = len(scores)
        counts = Counter(scores)

        score_distribution = []
        low_count = 0  # оценки 1 и 2

        for s in range(1, 6):
            count = counts.get(s, 0)
            percent = round((count / total_completions) * 100, 2) if total_completions > 0 else 0.0
            if s <= 2:
                low_count += count
            score_distribution.append({"score": s, "count": count, "percent": percent})

        rec_mood_trigger = (
            (low_count / total_completions) >= 0.60
            if total_completions > 0
            else False
        )

        return {
            "period": period,
            "start_date": start_date,
            "end_date": today,
            "total_completions": total_completions,
            "rec_mood_trigger": rec_mood_trigger,
            "score_distribution": score_distribution,
        }

    # ------------------------------------------------------------------
    # helpers для get_teams_mood
    # ------------------------------------------------------------------

    @staticmethod
    def _get_week_day_ranges(today: date):
        ranges = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            ranges.append((day, day, day.strftime("%d.%m")))
        return ranges

    @staticmethod
    def _get_month_week_ranges(today: date):
        ranges = []
        end = today
        for i in range(4):
            start = end - timedelta(days=6)
            label = f"Неделя {4 - i}"
            ranges.insert(0, (start, end, label))
            end = start - timedelta(days=1)
        return ranges

    @staticmethod
    def _get_year_month_ranges(today: date):
        ranges = []
        year = today.year
        month = today.month

        for _ in range(12):
            start = date(year, month, 1)
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            end = next_month - timedelta(days=1)

            label = start.strftime("%m.%Y")
            ranges.insert(0, (start, end, label))

            month -= 1
            if month == 0:
                month = 12
                year -= 1

        return ranges