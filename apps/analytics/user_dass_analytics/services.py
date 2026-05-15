from calendar import monthrange
from datetime import date, timedelta
from typing import Dict, List

from apps.assessments.dass.models import Dass9Result


MONTH_NAMES_RU = [
    "",
    "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
    "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек",
]


class UserDassStatisticsService:

    @staticmethod
    def _get_level(score: int) -> str:
        if 0 <= score <= 3:
            return "normal"

        if 4 <= score <= 5:
            return "moderate"

        return "high"

    @staticmethod
    def _check_recommendation(values: List[float]) -> bool:
        """
        Возвращает True, если есть два подряд периода,
        где значение больше 6.
        """
        for i in range(len(values) - 1):
            if values[i] > 6 and values[i + 1] > 6:
                return True

        return False

    @staticmethod
    def _build_metric_data(
        results: List[Dass9Result],
        field: str,
        metric_type: str,
    ) -> Dict:
        """
        Формирует данные по одной метрике:
        stress / anxiety / depression.

        results должны быть отсортированы от новых к старым.
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
            "recommendation_trigger": last_score >= 6,
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
                        "recommendation_trigger": False,
                    },
                    {
                        "type": "anxiety",
                        "score": 0,
                        "level": "normal",
                        "change": None,
                        "chart": [],
                        "recommendation_trigger": False,
                    },
                    {
                        "type": "depression",
                        "score": 0,
                        "level": "normal",
                        "change": None,
                        "chart": [],
                        "recommendation_trigger": False,
                    },
                ],
            }

        last_result = results[0]

        return {
            "date": last_result.date.isoformat(),
            "statistics": [
                UserDassStatisticsService._build_metric_data(
                    results,
                    "stress_score",
                    "stress",
                ),
                UserDassStatisticsService._build_metric_data(
                    results,
                    "anxiety_score",
                    "anxiety",
                ),
                UserDassStatisticsService._build_metric_data(
                    results,
                    "depression_score",
                    "depression",
                ),
            ],
        }

    @staticmethod
    def get_completion_stats(user_id: str) -> Dict:
        qs = Dass9Result.objects.filter(user_id=user_id).order_by("date")
        total_tests = qs.count()

        if total_tests == 0:
            return {
                "total_tests": 0,
                "completion_percent": 0.0,
                "recommendation_trigger": True,
            }

        first_date: date = qs.first().date
        today = date.today()

        days_since_start = (today - first_date).days + 1

        full_weeks = (days_since_start - 1) // 7
        days_in_current_window = days_since_start - full_weeks * 7

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

    @staticmethod
    def get_history(user_id: str, period: str) -> Dict:
        """
        Возвращает историю DASS9 по актуальным календарным периодам.

        period=week:
        - последние 7 календарных дней, включая сегодня

        period=month:
        - последние 4 недели по 7 дней

        period=year:
        - последние 12 месяцев

        Для каждого периода считаются средние значения:
        stress, anxiety, depression.
        """
        if period == "week":
            return UserDassStatisticsService._history_week(user_id)

        if period == "month":
            return UserDassStatisticsService._history_month(user_id)

        if period == "year":
            return UserDassStatisticsService._history_year(user_id)

        raise ValueError(
            f"Unknown period: {period!r}. "
            "Expected 'week', 'month' or 'year'."
        )

    @staticmethod
    def _avg_results_for_period(
        user_id: str,
        start: date,
        end: date,
    ) -> Dict[str, float]:
        """
        Считает средние значения stress/anxiety/depression за период.

        Если результатов нет, возвращает 0.0.
        """
        qs = Dass9Result.objects.filter(
            user_id=user_id,
            date__range=[start, end],
        )

        count = qs.count()

        if count == 0:
            return {
                "stress": 0.0,
                "anxiety": 0.0,
                "depression": 0.0,
            }

        stress = round(sum(r.stress_score for r in qs) / count, 2)
        anxiety = round(sum(r.anxiety_score for r in qs) / count, 2)
        depression = round(sum(r.depression_score for r in qs) / count, 2)

        return {
            "stress": stress,
            "anxiety": anxiety,
            "depression": depression,
        }

    @staticmethod
    def _build_response(period: str, points: List[Dict]) -> Dict:
        """
        Формирует общий ответ history.
        Также считает recommendation-флаги по двум подряд значениям > 6.
        """
        stress_values = [p["stress"] for p in points]
        anxiety_values = [p["anxiety"] for p in points]
        depression_values = [p["depression"] for p in points]

        check = UserDassStatisticsService._check_recommendation

        return {
            "period": period,
            "stress_recommendation": check(stress_values),
            "anxiety_recommendation": check(anxiety_values),
            "depression_recommendation": check(depression_values),
            "points": points,
        }

    @staticmethod
    def _history_week(user_id: str) -> Dict:
        """
        Последние 7 календарных дней.

        Например, если сегодня 2026-05-15:
        вернёт даты с 2026-05-09 по 2026-05-15.
        """
        today = date.today()
        start_day = today - timedelta(days=6)

        points = []

        for i in range(7):
            current_day = start_day + timedelta(days=i)

            values = UserDassStatisticsService._avg_results_for_period(
                user_id=user_id,
                start=current_day,
                end=current_day,
            )

            points.append({
                "label": current_day.isoformat(),
                "start_date": current_day,
                "end_date": current_day,
                "stress": values["stress"],
                "anxiety": values["anxiety"],
                "depression": values["depression"],
            })

        return UserDassStatisticsService._build_response("week", points)

    @staticmethod
    def _history_month(user_id: str) -> Dict:
        """
        Последние 4 недели по 7 дней.

        Неделя 1: today - 27 ... today - 21
        Неделя 2: today - 20 ... today - 14
        Неделя 3: today - 13 ... today - 7
        Неделя 4: today - 6  ... today
        """
        today = date.today()

        windows = []

        for i in range(3, -1, -1):
            end = today - timedelta(days=i * 7)
            start = end - timedelta(days=6)
            windows.append((start, end))

        points = []

        for index, (start, end) in enumerate(windows, start=1):
            values = UserDassStatisticsService._avg_results_for_period(
                user_id=user_id,
                start=start,
                end=end,
            )

            points.append({
                "label": f"Неделя {index}",
                "start_date": start,
                "end_date": end,
                "stress": values["stress"],
                "anxiety": values["anxiety"],
                "depression": values["depression"],
            })

        return UserDassStatisticsService._build_response("month", points)

    @staticmethod
    def _history_year(user_id: str) -> Dict:
        """
        Последние 12 месяцев.

        Текущий месяц обрезается по сегодняшнюю дату.
        Например, если сегодня 2026-05-15:
        Май 2026 будет иметь start_date=2026-05-01, end_date=2026-05-15.
        """
        today = date.today()

        months = []

        for i in range(11, -1, -1):
            month = today.month - i
            year = today.year

            while month <= 0:
                month += 12
                year -= 1

            start = date(year, month, 1)
            last_day = monthrange(year, month)[1]
            end = date(year, month, last_day)

            if end > today:
                end = today

            months.append((year, month, start, end))

        points = []

        for year, month, start, end in months:
            values = UserDassStatisticsService._avg_results_for_period(
                user_id=user_id,
                start=start,
                end=end,
            )

            points.append({
                "label": f"{MONTH_NAMES_RU[month]} {year}",
                "start_date": start,
                "end_date": end,
                "stress": values["stress"],
                "anxiety": values["anxiety"],
                "depression": values["depression"],
            })

        return UserDassStatisticsService._build_response("year", points)