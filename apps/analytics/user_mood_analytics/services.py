from calendar import monthrange
from datetime import date, timedelta
from typing import Dict, List, Tuple

from apps.assessments.mood.models import MoodResult


MONTH_NAMES_RU = [
    "", "Янв", "Фев", "Мар", "Апр", "Май", "Июн",
    "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"
]


class UserMoodAnalyticsService:

    @staticmethod
    def get_history(user_id: str, period: str) -> Dict:
        """
        Возвращает историю настроения пользователя.

        period="week"  -> 7 точек по дням.
        period="month" -> 4 точки по неделям, score = среднее за неделю.
        period="year"  -> 12 точек по месяцам, score = среднее за месяц.

        Во всех вариантах возвращается:
        - total_completions -> общее количество прохождений в выбранном периоде.
        - score_distribution -> распределение оценок 1-5.
        - rec_mood_trigger -> True, если 60%+ прохождений имеют score 1 или 2.
        - consecutive_low_trigger -> True, если есть два подряд прохождения со score <= 2.
        - points -> точки графика.
        """
        if period == "week":
            return UserMoodAnalyticsService._history_week(user_id)

        if period == "month":
            return UserMoodAnalyticsService._history_month(user_id)

        if period == "year":
            return UserMoodAnalyticsService._history_year(user_id)

        raise ValueError(
            f"Unknown period: {period!r}. Expected 'week', 'month' or 'year'."
        )

    # ------------------------------------------------------------------
    # Периоды
    # ------------------------------------------------------------------

    @staticmethod
    def _history_week(user_id: str) -> Dict:
        """
        Последние 7 дней, включая сегодня.

        Возвращает 7 точек:
        - 1 точка = 1 день
        - score = score за этот день
        - если данных нет, score = 0.0
        """
        today = date.today()
        start = today - timedelta(days=6)

        return UserMoodAnalyticsService._build_daily_response(
            user_id=user_id,
            start=start,
            end=today,
            period="week",
        )

    @staticmethod
    def _history_month(user_id: str) -> Dict:
        """
        Последние 4 недели, включая сегодня.

        Возвращает 4 точки:
        - 1 точка = 7 дней
        - score = средний score за неделю
        - если данных нет, score = 0.0
        """
        today = date.today()
        start = today - timedelta(days=27)

        ranges: List[Tuple[date, date]] = []
        current_start = start

        for index in range(4):
            current_end = current_start + timedelta(days=6)

            if index == 3:
                current_end = today

            ranges.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)

        return UserMoodAnalyticsService._build_grouped_response(
            user_id=user_id,
            ranges=ranges,
            period="month",
            label_type="week",
        )

    @staticmethod
    def _history_year(user_id: str) -> Dict:
        """
        Последние 12 месяцев, включая текущий месяц.

        Возвращает 12 точек:
        - 1 точка = 1 месяц
        - score = средний score за месяц
        - если данных нет, score = 0.0
        """
        today = date.today()

        months: List[Tuple[int, int]] = []

        year = today.year
        month = today.month

        for _ in range(12):
            months.append((year, month))

            month -= 1
            if month == 0:
                month = 12
                year -= 1

        months.reverse()

        ranges: List[Tuple[date, date]] = []

        for year, month in months:
            start = date(year, month, 1)
            end = date(year, month, monthrange(year, month)[1])

            if year == today.year and month == today.month:
                end = today

            ranges.append((start, end))

        return UserMoodAnalyticsService._build_grouped_response(
            user_id=user_id,
            ranges=ranges,
            period="year",
            label_type="month",
        )

    # ------------------------------------------------------------------
    # Week: 7 точек по дням
    # ------------------------------------------------------------------

    @staticmethod
    def _build_daily_response(
        user_id: str,
        start: date,
        end: date,
        period: str,
    ) -> Dict:
        results = list(
            MoodResult.objects
            .filter(user_id=user_id, date__gte=start, date__lte=end)
            .values("date", "score")
            .order_by("date")
        )

        score_by_date: Dict[date, int] = {
            row["date"]: row["score"]
            for row in results
        }

        points = []
        current = start

        while current <= end:
            score = score_by_date.get(current)

            points.append({
                "label": current.isoformat(),
                "start_date": current,
                "end_date": current,
                "score": float(score) if score is not None else 0.0,
            })

            current += timedelta(days=1)

        actual_scores = [row["score"] for row in results]
        total_completions = len(actual_scores)

        return UserMoodAnalyticsService._build_response_base(
            period=period,
            total_completions=total_completions,
            actual_scores=actual_scores,
            score_by_date=score_by_date,
            start=start,
            end=end,
            points=points,
        )

    # ------------------------------------------------------------------
    # Month / Year: точки по группам
    # ------------------------------------------------------------------

    @staticmethod
    def _build_grouped_response(
        user_id: str,
        ranges: List[Tuple[date, date]],
        period: str,
        label_type: str,
    ) -> Dict:
        start = ranges[0][0]
        end = ranges[-1][1]

        results = list(
            MoodResult.objects
            .filter(user_id=user_id, date__gte=start, date__lte=end)
            .values("date", "score")
            .order_by("date")
        )

        score_by_date: Dict[date, int] = {
            row["date"]: row["score"]
            for row in results
        }

        points = []

        for index, (range_start, range_end) in enumerate(ranges, start=1):
            scores = [
                row["score"]
                for row in results
                if range_start <= row["date"] <= range_end
            ]

            avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0

            if label_type == "week":
                label = f"Неделя {index}"
            elif label_type == "month":
                label = f"{MONTH_NAMES_RU[range_start.month]} {range_start.year}"
            else:
                label = range_start.isoformat()

            points.append({
                "label": label,
                "start_date": range_start,
                "end_date": range_end,
                "score": avg_score,
            })

        actual_scores = [row["score"] for row in results]
        total_completions = len(actual_scores)

        return UserMoodAnalyticsService._build_response_base(
            period=period,
            total_completions=total_completions,
            actual_scores=actual_scores,
            score_by_date=score_by_date,
            start=start,
            end=end,
            points=points,
        )

    # ------------------------------------------------------------------
    # Общая сборка ответа
    # ------------------------------------------------------------------

    @staticmethod
    def _build_response_base(
        period: str,
        total_completions: int,
        actual_scores: List[int],
        score_by_date: Dict[date, int],
        start: date,
        end: date,
        points: List[Dict],
    ) -> Dict:
        score_distribution = UserMoodAnalyticsService._calc_distribution(
            actual_scores,
            total_completions,
        )

        rec_mood_trigger = UserMoodAnalyticsService._check_rec_mood_trigger(
            actual_scores,
            total_completions,
        )

        consecutive_low_trigger = UserMoodAnalyticsService._check_consecutive_low(
            score_by_date,
            start,
            end,
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
        Возвращает распределение по score 1-5.

        percent = count / total * 100.
        Если total == 0, percent = 0.0.
        """
        from collections import Counter

        counts = Counter(scores)
        distribution = []

        for score in range(1, 6):
            count = counts.get(score, 0)
            percent = round((count / total) * 100, 2) if total > 0 else 0.0

            distribution.append({
                "score": score,
                "count": count,
                "percent": percent,
            })

        return distribution

    @staticmethod
    def _check_rec_mood_trigger(scores: List[int], total: int) -> bool:
        """
        True, если 60% или больше прохождений имеют score 1 или 2.
        """
        if total == 0:
            return False

        low_count = sum(1 for score in scores if score <= 2)

        return (low_count / total) >= 0.60

    @staticmethod
    def _check_consecutive_low(
        score_by_date: Dict[date, int],
        start: date,
        end: date,
    ) -> bool:
        """
        True, если есть два подряд фактических прохождения со score <= 2.

        Проверяются только дни, когда пользователь реально проходил оценку.
        Дни без данных пропускаются.
        """
        actual_dates = sorted(
            current_date
            for current_date in score_by_date.keys()
            if start <= current_date <= end
        )

        for index in range(len(actual_dates) - 1):
            first_date = actual_dates[index]
            second_date = actual_dates[index + 1]

            if score_by_date[first_date] <= 2 and score_by_date[second_date] <= 2:
                return True

        return False