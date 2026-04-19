from calendar import monthrange
from datetime import date, timedelta
from typing import Dict, List

from apps.assessments.mood.models import MoodResult

MONTH_NAMES_RU = [
    "", "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
    "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
]


class UserMoodAnalyticsService:

    @staticmethod
    def get_history(user_id: str, period: str) -> Dict:
        """
        Возвращает аналитику настроения (1–5) для пользователя.

        period="week"  → 7 дней (каждый день — отдельная точка).
        period="month" → 31 день (каждый день — отдельная точка).
        period="year"  → 365 дней (каждый день — отдельная точка).

        Для всех периодов:
        - total_completions — общее число фактических прохождений в диапазоне.
        - score_distribution — для каждой оценки (1–5): количество и процент
          от total_completions.
        - rec_mood_trigger — True, если 60%+ прохождений имели оценку 1 или 2.
        - consecutive_low_trigger — True, если есть хотя бы 2 даты подряд с
          оценкой <= 2.
        - points — список точек (одна на день). Если в этот день прохождения
          не было — score = 0.0.
        """
        if period == "week":
            return UserMoodAnalyticsService._history_week(user_id)
        if period == "month":
            return UserMoodAnalyticsService._history_month(user_id)
        if period == "year":
            return UserMoodAnalyticsService._history_year(user_id)
        raise ValueError(f"Unknown period: {period!r}. Expected 'week', 'month' or 'year'.")

    # ------------------------------------------------------------------
    # Периоды
    # ------------------------------------------------------------------

    @staticmethod
    def _history_week(user_id: str) -> Dict:
        """7 последних дней (сегодня + 6 предыдущих) — по одной точке на день."""
        today = date.today()
        start = today - timedelta(days=6)
        return UserMoodAnalyticsService._build_daily_response(user_id, start, today, "week")

    @staticmethod
    def _history_month(user_id: str) -> Dict:
        """31 последний день — по одной точке на день."""
        today = date.today()
        start = today - timedelta(days=30)
        return UserMoodAnalyticsService._build_daily_response(user_id, start, today, "month")

    @staticmethod
    def _history_year(user_id: str) -> Dict:
        """365 последних дней — по одной точке на день."""
        today = date.today()
        start = today - timedelta(days=364)
        return UserMoodAnalyticsService._build_daily_response(user_id, start, today, "year")

    # ------------------------------------------------------------------
    # Общий строитель (все периоды — по дням)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_daily_response(user_id: str, start: date, end: date, period: str) -> Dict:
        """
        Формирует ответ для любого периода с разбивкой по дням.

        Запрашивает результаты из БД одним запросом, затем раскладывает
        по ключу date в словарь для O(1) доступа при обходе дат.
        """
        results = list(
            MoodResult.objects
            .filter(user_id=user_id, date__gte=start, date__lte=end)
            .values("date", "score")
            .order_by("date")
        )

        # Словарь date → score для быстрого доступа
        score_by_date: Dict[date, int] = {row["date"]: row["score"] for row in results}

        # Генерируем одну точку на каждый день в диапазоне [start, end]
        points = []
        current = start
        while current <= end:
            score = score_by_date.get(current, None)
            points.append({
                "label": current.isoformat(),
                "start_date": current,
                "end_date": current,
                "score": float(score) if score is not None else 0.0,
            })
            current += timedelta(days=1)

        # Считаем статистику только по фактическим прохождениям
        actual_scores = [row["score"] for row in results]
        total_completions = len(actual_scores)

        score_distribution = UserMoodAnalyticsService._calc_distribution(
            actual_scores, total_completions
        )

        rec_mood_trigger = UserMoodAnalyticsService._check_rec_mood_trigger(
            actual_scores, total_completions
        )

        consecutive_low_trigger = UserMoodAnalyticsService._check_consecutive_low(
            score_by_date, start, end
        )

        return {
            "period": period,
            "total_completions": total_completions,
            "score_distribution": score_distribution,
            "rec_mood_trigger": rec_mood_trigger,
            "consecutive_low_trigger": consecutive_low_trigger,
            "points": points,
        }

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    @staticmethod
    def _calc_distribution(scores: List[int], total: int) -> List[Dict]:
        """
        Возвращает список из 5 элементов (по одному на оценку 1–5).
        percent = count / total * 100, округлённый до 2 знаков.
        При total == 0 — все проценты равны 0.
        """
        from collections import Counter
        counts = Counter(scores)
        distribution = []
        for s in range(1, 6):
            count = counts.get(s, 0)
            percent = round((count / total) * 100, 2) if total > 0 else 0.0
            distribution.append({"score": s, "count": count, "percent": percent})
        return distribution

    @staticmethod
    def _check_rec_mood_trigger(scores: List[int], total: int) -> bool:
        """
        Триггер 1: True если 60% и более прохождений имели оценку 1 или 2.
        При total == 0 возвращает False.
        """
        if total == 0:
            return False
        low_count = sum(1 for s in scores if s <= 2)
        return (low_count / total) >= 0.60

    @staticmethod
    def _check_consecutive_low(
        score_by_date: Dict[date, int],
        start: date,
        end: date,
    ) -> bool:
        """
        Триггер 2: True если есть хотя бы две идущие подряд даты
        (в которые было прохождение) с оценкой <= 2.

        Сравниваются только даты, когда пользователь реально проходил тест,
        пропущенные дни не учитываются.
        """
        # Берём только даты с фактическими прохождениями, сортируем
        actual_dates = sorted(d for d, s in score_by_date.items() if start <= d <= end)

        for i in range(len(actual_dates) - 1):
            d1 = actual_dates[i]
            d2 = actual_dates[i + 1]
            if score_by_date[d1] <= 2 and score_by_date[d2] <= 2:
                return True
        return False