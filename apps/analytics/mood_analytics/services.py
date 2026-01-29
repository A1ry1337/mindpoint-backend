from datetime import date, timedelta
from typing import List, Optional, Dict
from uuid import UUID

from django.db.models import Count, Avg
from django.utils import timezone

from collections import defaultdict

from apps.assessments.mood.models import MoodResult
from apps.manager.management.models import Team

class MoodStatisticsService:

    @staticmethod
    def get_teams_mood(
        manager_id: int,
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
        period = period or "week"
        period = period.lower()

        today = timezone.now().date()

        if period == "week":
            ranges = MoodStatisticsService._get_week_day_ranges(today)
        elif period == "month":
            ranges = MoodStatisticsService._get_month_week_ranges(today)
        elif period == "year":
            ranges = MoodStatisticsService._get_year_month_ranges(today)
        else:
            # по умолчанию неделя
            ranges = MoodStatisticsService._get_week_day_ranges(today)

        # команды менеджера
        teams_qs = Team.objects.filter(manager_id=manager_id)

        if team_id:
            teams_qs = teams_qs.filter(id=team_id)

        teams = list(teams_qs)

        result_items = []

        for team in teams:
            team_points = []

            for idx, (start_date, end_date, label) in enumerate(ranges):
                members = team.members.all()

                mood_qs = (
                    MoodResult.objects
                    .filter(
                        user__in=members,
                        date__gte=start_date,
                        date__lte=end_date,
                    )
                    .values("score")
                    .annotate(count=Count("id"))
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
                    scores_list = [
                        {
                            "score": s,
                            "count": score_map.get(s, 0),
                        }
                        for s in range(1, 6)
                    ]
                    point_data["scores"] = scores_list

                team_points.append(point_data)

            result_items.append({
                "team_id": team.id,
                "team_name": team.name,
                "points": team_points,
            })

        return {"items": result_items}

    @staticmethod
    def _get_week_day_ranges(today: date):
        """
        7 дней: сегодня и 6 предыдущих.
        Возвращаем список (start_date, end_date, label) для каждого дня.
        """
        ranges = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            ranges.append((day, day, day.strftime("%d.%m")))
        return ranges

    @staticmethod
    def _get_month_week_ranges(today: date):
        """
        4 недели: текущая и 3 предыдущие.
        Каждая неделя = интервал длиной 7 дней.
        Отсчёт от today назад.
        """
        ranges = []
        # текущая неделя — [today-6, today]
        end = today
        for i in range(4):
            start = end - timedelta(days=6)
            label = f"Неделя {4 - i}"  # Неделя 4 (самая старая), Неделя 1 (самая свежая)
            ranges.insert(0, (start, end, label))
            end = start - timedelta(days=1)
        return ranges

    @staticmethod
    def _get_year_month_ranges(today: date):
        """
        12 месяцев: текущий и 11 предыдущих.
        Для простоты считаем:
          start = первое число месяца
          end   = последнее число месяца
        """
        ranges = []
        year = today.year
        month = today.month

        for _ in range(12):
            start = date(year, month, 1)
            # вычисляем конец месяца
            if month == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, month + 1, 1)
            end = next_month - timedelta(days=1)

            label = start.strftime("%m.%Y")
            ranges.insert(0, (start, end, label))

            # предыдущий месяц
            month -= 1
            if month == 0:
                month = 12
                year -= 1

        return ranges


    PERIOD_TO_DAYS = {
        "day": 1,
        "week": 7,
        "month": 31,
        "year": 365,
    }

    @staticmethod
    def get_mood_distribution(
        manager_id: int,
        period: str,
        team_ids: Optional[List[UUID]] = None,
    ) -> Dict:

        days = MoodStatisticsService.PERIOD_TO_DAYS.get(period, 7)

        today = timezone.now().date()
        start_date = today - timedelta(days=days - 1)

        teams_qs = Team.objects.filter(manager_id=manager_id)
        if team_ids:
            teams_qs = teams_qs.filter(id__in=team_ids)

        members = (
            Team.objects
            .filter(id__in=teams_qs.values_list("id", flat=True))
            .values_list("members", flat=True)
            .distinct()
        )

        total_members = len(members)

        if total_members == 0:
            return {"period": period, "points": []}

        # средний скор пользователя за период
        user_avg_scores = (
            MoodResult.objects
            .filter(
                user__in=members,
                date__gte=start_date,
                date__lte=today,
            )
            .values("user")
            .annotate(avg_score=Avg("score"))
        )

        buckets = defaultdict(int)

        for row in user_avg_scores:
            score = round(row["avg_score"])
            score = max(1, min(5, int(score)))
            buckets[score] += 1

        scores = []
        for s in range(1, 6):
            percent = (buckets.get(s, 0) / total_members) * 100
            scores.append({
                "score": s,
                "percent": round(percent, 2),
            })

        return {
            "period": period,
            "points": [
                {
                    "period_label": f"Последние {days} дней",
                    "start_date": start_date,
                    "end_date": today,
                    "total_members": total_members,
                    "scores": scores,
                }
            ],
        }