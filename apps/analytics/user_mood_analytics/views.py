from ninja import Router, Query
from ninja.errors import HttpError

from apps.auth_user.permissions import JWTAuth
from apps.analytics.user_mood_analytics.schemas import UserMoodHistoryOut
from apps.analytics.user_mood_analytics.services import UserMoodAnalyticsService


router = Router(tags=["Аналитика настроения пользователя"])


@router.get("/history", response=UserMoodHistoryOut, auth=JWTAuth())
def get_mood_history(
    request,
    period: str = Query(
        "week",
        description=(
            "week | month | year. "
            "week = 7 точек по дням, "
            "month = 4 точки по неделям, "
            "year = 12 точек по месяцам"
        ),
    ),
):
    """
    Возвращает историю настроения пользователя.

    ### Параметры

    - **period**: период аналитики.
        - `week` — последние 7 дней, 7 точек.
        - `month` — последние 4 недели, 4 точки, среднее за неделю.
        - `year` — последние 12 месяцев, 12 точек, среднее за месяц.

    ### Ответ

    - **total_completions** — общее количество прохождений в периоде.
    - **score_distribution** — распределение по оценкам 1-5:
        - `count` — количество прохождений с этой оценкой.
        - `percent` — процент от `total_completions`.
    - **rec_mood_trigger** — `true`, если 60% или больше прохождений имеют score 1 или 2.
    - **consecutive_low_trigger** — `true`, если есть два подряд прохождения со score <= 2.
    - **points** — точки графика:
        - для `week` — 7 дневных точек;
        - для `month` — 4 недельные точки;
        - для `year` — 12 месячных точек.
    """
    if period not in ("week", "month", "year"):
        raise HttpError(400, "period must be one of: week, month, year")

    user_id = request.auth["user_id"]

    return UserMoodAnalyticsService.get_history(
        user_id=user_id,
        period=period,
    )