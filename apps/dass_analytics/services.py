from datetime import date, timedelta
from typing import Dict, Optional, List
from django.db.models import Avg, F
from django.shortcuts import get_object_or_404

from apps.assessments.dass.models import Dass9Result
from apps.auth_user.models import User
from apps.dass_analytics.utils import DassAnalyticsUtils
from apps.manager.management.models import Team


class StatisticsService:

    @staticmethod
    def _calc_change(old_value: float, new_value: float) -> Dict:
        if old_value == 0:
            return {"direction": "up" if new_value > 0 else "neutral", "percent": None}
        diff = new_value - old_value
        percent = abs((diff / old_value) * 100)
        if diff > 0:
            direction = "up"
        elif diff < 0:
            direction = "down"
        else:
            direction = "neutral"
        return {"direction": direction, "percent": round(percent, 2)}

    @staticmethod
    def get_ips_overview(manager_id: str,
                              team_id: Optional[str] = None,
                              period: str = "day") -> Dict[str, any]:
        start, end, prev_start, prev_end = DassAnalyticsUtils.get_current_and_previous_period_dates(period)

        if team_id:
            team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
            member_ids = team.members.values_list("id", flat=True)
        else:
            member_ids = User.objects.filter(manager_id=manager_id).values_list("id", flat=True)

        # Текущий и предыдущий периоды
        qs = Dass9Result.objects.filter(user_id__in=member_ids, date__range=[start, end])
        prev_qs = Dass9Result.objects.filter(user_id__in=member_ids, date__range=[prev_start, prev_end])

        # Средние значения
        curr_avg = qs.aggregate(
            avg_anxiety=Avg("anxiety_score"),
            avg_depression=Avg("depression_score"),
            avg_stress=Avg("stress_score")
        )
        prev_avg = prev_qs.aggregate(
            avg_anxiety=Avg("anxiety_score"),
            avg_depression=Avg("depression_score"),
            avg_stress=Avg("stress_score")
        )

        def safe_value(val): return val or 0.0

        curr_anxiety = safe_value(curr_avg["avg_anxiety"])
        curr_depression = safe_value(curr_avg["avg_depression"])
        curr_stress = safe_value(curr_avg["avg_stress"])
        prev_anxiety = safe_value(prev_avg["avg_anxiety"])
        prev_depression = safe_value(prev_avg["avg_depression"])
        prev_stress = safe_value(prev_avg["avg_stress"])

        curr_ips_raw = (curr_anxiety + curr_depression + curr_stress) / 3 if any([curr_anxiety, curr_depression, curr_stress]) else 0
        prev_ips_raw = (prev_anxiety + prev_depression + prev_stress) / 3 if any([prev_anxiety, prev_depression, prev_stress]) else 0

        curr_ips = 100 - (curr_ips_raw / 27) * 100 if curr_ips_raw != 0 else 0
        prev_ips = 100 - (prev_ips_raw / 27) * 100 if prev_ips_raw != 0 else 0

        stats = [
            {
                "type": "ips",
                "score": round(curr_ips, 2),
                "max_score": 100.0,
                "change": StatisticsService._calc_change(prev_ips, curr_ips)
            },
            {
                "type": "anxiety",
                "score": round(curr_anxiety, 2),
                "max_score": 9.0,
                "change": StatisticsService._calc_change(prev_anxiety, curr_anxiety)
            },
            {
                "type": "depression",
                "score": round(curr_depression, 2),
                "max_score": 9.0,
                "change": StatisticsService._calc_change(prev_depression, curr_depression)
            },
            {
                "type": "stress",
                "score": round(curr_stress, 2),
                "max_score": 9.0,
                "change": StatisticsService._calc_change(prev_stress, curr_stress)
            },
        ]

        return {
            "period": period,
            "statistics": stats
        }

    @staticmethod
    def get_test_count(manager_id: str,
                       team_id: str,
                       period: str = "week") -> Dict[str, any]:
        """
        Возвращает количество прохождений теста DASS9 за последние 4 периода
        (дня, недели, месяца или года) для выбранной команды.
        Если данных нет — добавляется сообщение.
        """
        team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
        member_ids = team.members.values_list("id", flat=True)

        periods: List[Dict] = []

        for offset in range(4):
            start, end = DassAnalyticsUtils.get_period_dates(period, offset)
            count = Dass9Result.objects.filter(
                user_id__in=member_ids,
                date__range=[start, end]
            ).count()

            entry = {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "test_count": count,
            }

            if count == 0:
                entry["message"] = "Данные ещё не собраны"

            periods.append(entry)

        # Сортируем по возрастанию (от старого к новому)
        periods.reverse()

        return {"period": period, "periods": periods}