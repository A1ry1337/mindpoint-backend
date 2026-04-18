from datetime import date, timedelta
from typing import Dict, List

from apps.assessments.dass.models import Dass9Result

MONTH_NAMES_RU = [
    "", "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
    "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
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
        Возвращает True если есть хотя бы две точки подряд со значением > 6.
        Работает одинаково для week/month/year — просто смотрит на список значений.
        """
        for i in range(len(values) - 1):
            if values[i] > 6 and values[i + 1] > 6:
                return True
        return False

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

    @staticmethod
    def get_history(user_id: str, period: str) -> Dict:
        """
        Возвращает историю показателей стресса, тревоги и депрессии по периодам,
        а также три булевых триггера рекомендаций.

        Триггер = True если хотя бы две точки подряд имеют значение > 6.
        Логика одинакова для всех периодов.

        period="week"  → последние 7 прохождений как отдельные точки (от старого к новому).
        period="month" → 4 последних 7-дневных окна (от старого к новому), среднее по окну.
        period="year"  → 12 последних календарных месяцев (от старого к новому), среднее по месяцу.
        """
        if period == "week":
            return UserDassStatisticsService._history_week(user_id)
        if period == "month":
            return UserDassStatisticsService._history_month(user_id)
        if period == "year":
            return UserDassStatisticsService._history_year(user_id)
        raise ValueError(f"Unknown period: {period!r}. Expected 'week', 'month' or 'year'.")

    # --- helpers ---

    @staticmethod
    def _build_response(period: str, points: List[Dict]) -> Dict:
        """
        Собирает финальный ответ: добавляет три recommendation-триггера,
        вычисленных по готовому списку точек.
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
        """7 последних прохождений как отдельные точки (от старого к новому)."""
        results = list(
            Dass9Result.objects
            .filter(user_id=user_id)
            .order_by("-date", "-id")[:7]
        )
        results.reverse()  # старые → новые

        points = [
            {
                "label": r.date.isoformat(),
                "start_date": r.date,
                "end_date": r.date,
                "stress": float(r.stress_score),
                "anxiety": float(r.anxiety_score),
                "depression": float(r.depression_score),
            }
            for r in results
        ]

        return UserDassStatisticsService._build_response("week", points)

    @staticmethod
    def _history_month(user_id: str) -> Dict:
        """
        4 последних 7-дневных окна (от старого к новому).
        Окно 1: [today-27 .. today-21]
        Окно 2: [today-20 .. today-14]
        Окно 3: [today-13 .. today-7]
        Окно 4: [today-6  .. today]
        """
        today = date.today()
        windows = []
        for i in range(3, -1, -1):  # 3,2,1,0 → от старого к новому
            end = today - timedelta(days=i * 7)
            start = end - timedelta(days=6)
            windows.append((start, end))

        points = []
        for idx, (start, end) in enumerate(windows, start=1):
            qs = Dass9Result.objects.filter(
                user_id=user_id,
                date__range=[start, end]
            )
            count = qs.count()
            if count:
                stress = round(sum(r.stress_score for r in qs) / count, 2)
                anxiety = round(sum(r.anxiety_score for r in qs) / count, 2)
                depression = round(sum(r.depression_score for r in qs) / count, 2)
            else:
                stress = anxiety = depression = 0.0

            points.append({
                "label": f"Неделя {idx}",
                "start_date": start,
                "end_date": end,
                "stress": stress,
                "anxiety": anxiety,
                "depression": depression,
            })

        return UserDassStatisticsService._build_response("month", points)

    @staticmethod
    def _history_year(user_id: str) -> Dict:
        """
        12 последних календарных месяцев (от самого старого к текущему).
        Текущий месяц — данные с 1-го числа по сегодня.
        """
        from calendar import monthrange

        today = date.today()
        months = []

        for i in range(11, -1, -1):  # 11..0 → от старого к новому
            month = today.month - i
            year = today.year
            while month <= 0:
                month += 12
                year -= 1

            start = date(year, month, 1)
            last_day = monthrange(year, month)[1]
            end = date(year, month, last_day)
            if end > today:
                end = today  # текущий месяц — до сегодня

            months.append((year, month, start, end))

        points = []
        for year, month, start, end in months:
            qs = Dass9Result.objects.filter(
                user_id=user_id,
                date__range=[start, end]
            )
            count = qs.count()
            if count:
                stress = round(sum(r.stress_score for r in qs) / count, 2)
                anxiety = round(sum(r.anxiety_score for r in qs) / count, 2)
                depression = round(sum(r.depression_score for r in qs) / count, 2)
            else:
                stress = anxiety = depression = 0.0

            points.append({
                "label": f"{MONTH_NAMES_RU[month]} {year}",
                "start_date": start,
                "end_date": end,
                "stress": stress,
                "anxiety": anxiety,
                "depression": depression,
            })

        return UserDassStatisticsService._build_response("year", points)
