from datetime import date, timedelta
from typing import Dict, Optional
from django.db.models import Avg, F
from django.shortcuts import get_object_or_404

from apps.assessments.dass.models import Dass9Result
from apps.auth_user.models import User
from apps.manager.management.models import Team

class StatisticsService:
    @staticmethod
    def _get_period_dates(period: str):
        today = date.today()
        if period == "day":
            start = today
            prev_start = today - timedelta(days=1)
            prev_end = today - timedelta(days=1)
        elif period == "week":
            start = today - timedelta(days=7)
            prev_start = today - timedelta(days=14)
            prev_end = today - timedelta(days=7)
        elif period == "month":
            start = today.replace(day=1)
            prev_month_end = start - timedelta(days=1)
            prev_start = prev_month_end.replace(day=1)
            prev_end = prev_month_end
        elif period == "year":
            start = date(today.year, 1, 1)
            prev_start = date(today.year - 1, 1, 1)
            prev_end = date(today.year - 1, 12, 31)
        else:
            raise ValueError("Invalid period")
        return start, today, prev_start, prev_end

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
    def get_ips_statistics(manager_id: str,
                           team_id: Optional[str] = None,
                           period: str = "day") -> Dict[str, any]:
        """
        Возвращает средний индекс психоэмоционального состояния (IPS)
        за указанный период и процент изменения относительно предыдущего.
        """
        start, end, prev_start, prev_end = StatisticsService._get_period_dates(period)

        if team_id:
            team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
            member_ids = team.members.values_list("id", flat=True)
        else:
            member_ids = User.objects.filter(manager_id=manager_id).values_list("id", flat=True)

        # Текущий период
        qs = Dass9Result.objects.filter(user_id__in=member_ids, date__range=[start, end])
        curr_ips = (
                qs.annotate(total=(F("depression_score") + F("stress_score") + F("anxiety_score")) / 3)
                .aggregate(avg_ips=Avg("total"))["avg_ips"] or 0
        )

        if curr_ips != 0:
            curr_ips = 100 - (curr_ips / 27) * 100

        # Предыдущий период
        prev_qs = Dass9Result.objects.filter(user_id__in=member_ids, date__range=[prev_start, prev_end])
        prev_ips = (
                prev_qs.annotate(total=(F("depression_score") + F("stress_score") + F("anxiety_score")) / 3)
                .aggregate(avg_ips=Avg("total"))["avg_ips"] or 0
        )

        if prev_ips != 0:
            prev_ips = 100 - (prev_ips / 27) * 100

        change = StatisticsService._calc_change(prev_ips, curr_ips)

        return {
            "period": period,
            "ips_score": round(curr_ips, 2),
            "ips_max_score": 100,
            "change": change,
        }
