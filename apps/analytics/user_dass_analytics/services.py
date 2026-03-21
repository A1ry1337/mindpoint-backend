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
    def _get_recommendation_trigger(score: int) -> bool:
        return score >= 6

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
            "recommendation_trigger": UserDassStatisticsService._get_recommendation_trigger(last_score)
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