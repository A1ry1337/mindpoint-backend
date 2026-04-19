from ninja import Router, Query
from ninja.errors import HttpError

from apps.auth_user.permissions import JWTAuth
from apps.analytics.user_mood_analytics.schemas import UserMoodHistoryOut
from apps.analytics.user_mood_analytics.services import UserMoodAnalyticsService

router = Router(tags=["Аналитика настроения для пользователя"])


@router.get("/history", response=UserMoodHistoryOut, auth=JWTAuth())
def get_mood_history(
    request,
    period: str = Query("week", description="week | month | year"),
):
    """
    Возвращает аналитику настроения (1–5) текущего пользователя.

    ### Параметры
    - **period**: период анализа.
        - `week`  — последние 7 дней  → 7 точек
        - `month` — последние 31 день → 31 точка
        - `year`  — последние 365 дней → 365 точек

    ### Ответ
    - **total_completions** — число фактических прохождений в периоде.
    - **score_distribution** — список из 5 элементов (оценки 1–5):
        - `count` — количество прохождений с такой оценкой.
        - `percent` — доля от `total_completions` в процентах (0–100).
          Пример: 10 прохождений, по 2 на каждую оценку → 20% каждой.
    - **rec_mood_trigger** — `true`, если 60% и более прохождений
      имели оценку 1 или 2.
    - **consecutive_low_trigger** — `true`, если есть хотя бы две
      даты подряд (среди дат с фактическими прохождениями) с оценкой ≤ 2.
    - **points** — список точек графика (одна на каждый день диапазона):
        - `label` — дата в формате `YYYY-MM-DD`.
        - `start_date` / `end_date` — совпадают (один день).
        - `score` — оценка за этот день; `0.0` если прохождения не было.
    """
    if period not in ("week", "month", "year"):
        raise HttpError(400, "period must be one of: week, month, year")

    user_id = request.auth["user_id"]
    return UserMoodAnalyticsService.get_history(user_id=user_id, period=period)