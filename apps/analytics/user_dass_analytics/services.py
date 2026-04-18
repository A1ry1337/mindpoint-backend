from datetime import date
from typing import Dict, List

from apps.assessments.dass.models import Dass9Result


class UserDassStatisticsService:

    @staticmethod
    def _get_level(score: int) -> str:
        if 0 <= score <= 3:
            return "normal"
        if 4 <= score <= 5:
            return "moderate"
        return "high"

    @staticmethod
    def _build_metric_data(results: List[Dass9Result], field: str, metric_type: str) -> Dict:
        """
        results ожидаются в порядке от нового к старому.
        """
        last_score = getattr(results[0], field)

        last_seven = results[:7]
        chart = [getattr(item, field) for item in reversed(last_seven)]

        change = None
        if len(results) > 1:
            prev_score = getattr(results[1], field)
            change = last_score - prev_score

        if len(results) == 1:
            chart = []

        return {
            "type": metric_type,
            "score": last_score,
            "level": UserDassStatisticsService._get_level(last_score),
            "change": change,
            "chart": chart,
            "recommendation_trigger": last_score >= 6
        }

    @staticmethod
    def get_last_result(user_id: str) -> Dict:
        results = list(
            Dass9Result.objects
            .filter(user_id=user_id)
            .order_by("-date", "-id")[:7]
        )

        if not results:
            return {
                "date": "",
                "statistics": [
                    {
                        "type": "stress",
                        "score": 0,
                        "level": "normal",
                        "change": None,
                        "chart": [],
                        "recommendation_trigger": False
                    },
                    {
                        "type": "anxiety",
                        "score": 0,
                        "level": "normal",
                        "change": None,
                        "chart": [],
                        "recommendation_trigger": False
                    },
                    {
                        "type": "depression",
                        "score": 0,
                        "level": "normal",
                        "change": None,
                        "chart": [],
                        "recommendation_trigger": False
                    },
                ]
            }

        last_result = results[0]

        return {
            "date": last_result.date.isoformat(),
            "statistics": [
                UserDassStatisticsService._build_metric_data(results, "stress_score", "stress"),
                UserDassStatisticsService._build_metric_data(results, "anxiety_score", "anxiety"),
                UserDassStatisticsService._build_metric_data(results, "depression_score", "depression"),
            ]
        }

    @staticmethod
    def get_completion_stats(user_id: str) -> Dict:
        qs = Dass9Result.objects.filter(user_id=user_id).order_by("date")
        total_tests = qs.count()

        if total_tests == 0:
            return {"total_tests": 0, "completion_percent": 0.0}

        first_date: date = qs.first().date
        today = date.today()

        # Количество дней с первого прохождения включительно
        days_since_start = (today - first_date).days + 1  # +1 чтобы включить сам день старта

        # Полных закрытых 7-дневных окон
        full_weeks = (days_since_start - 1) // 7

        # Дней, прошедших в текущем (незакрытом) окне (1..7)
        days_in_current_window = days_since_start - full_weeks * 7

        # Знаменатель: закрытые окна по 5 тестов + пропорция текущего окна
        expected = full_weeks * 5 + (days_in_current_window / 7) * 5

        if expected == 0:
            completion_percent = 0.0
        else:
            completion_percent = round((total_tests / expected) * 100, 2)

        return {
            "total_tests": total_tests,
            "completion_percent": completion_percent,
            "recommendation_trigger": completion_percent < 30,
        }