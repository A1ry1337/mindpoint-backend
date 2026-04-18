from ninja import Router, Query
from ninja.errors import HttpError

from apps.auth_user.permissions import JWTAuth
from apps.analytics.user_dass_analytics.schemas import UserLastDassResultOut, UserDassCompletionStatsOut, \
    UserDassHistoryOut
from apps.analytics.user_dass_analytics.services import UserDassStatisticsService

router = Router(tags=["Аналитика DASS для пользователя"])


@router.get("/last_result", response=UserLastDassResultOut, auth=JWTAuth())
def get_last_result(request):
    """
    Возвращает результат последнего прохождения теста DASS9 для текущего пользователя.

    Для каждой шкалы (стресс, тревога, депрессия) возвращается:
    - score — количество баллов на последнем тестировании (0–9)
    - level — уровень:
        normal
        moderate
        high
    - change — изменение относительно предыдущего прохождения (разница в баллах).
      Если прохождение только одно — change = null.
    - chart — массив значений за последние 7 прохождений (от старого к новому).
      Если прохождений меньше 7 — возвращаются фактические данные.
      Если прохождение только одно — chart = [].
    - recommendation_trigger — флаг рекомендации.
      True, если значение по шкале на последнем тестировании >= 6, иначе False.

    Также возвращается:
    - date — дата последнего прохождения теста.
    """
    user_id = request.auth["user_id"]
    return UserDassStatisticsService.get_last_result(user_id=user_id)


@router.get("/completion_stats", response=UserDassCompletionStatsOut, auth=JWTAuth())
def get_completion_stats(request):
    """
    Возвращает статистику прохождения тестов DASS9 за всё время.

    - total_tests — общее количество прохождений.
    - completion_percent — процент выполнения норматива.

    Норматив: 5 тестов за каждые 7 дней, отсчёт с даты первого прохождения.
    Текущая (незакрытая) неделя учитывается пропорционально прошедшим дням.

    Пример: первый тест 1 апреля, сегодня 19 апреля (19 дней).
    Это 2 полных недели (×5 = 10 тестов) + 5 дней из третьей (5/7×5 ≈ 3.57).
    Итого ожидается ≈ 13.57 тестов.
    Если пройдено 10 — completion_percent ≈ 73.7%.

    Если тестов не было — возвращает total_tests=0, completion_percent=0.0.
    """
    user_id = request.auth["user_id"]
    return UserDassStatisticsService.get_completion_stats(user_id=user_id)


@router.get("/history", response=UserDassHistoryOut, auth=JWTAuth())
def get_history(
        request,
        period: str = Query("week", description="week | month | year"),
):
    """
    Возвращает историю показателей стресса, тревоги и депрессии по периодам.

    **period=week** — последние 7 прохождений как отдельные точки (от старого к новому).
    - label      = дата прохождения, например "2025-04-13"
    - start_date = end_date = дата прохождения
    - stress / anxiety / depression — фактические баллы этого прохождения

    **period=month** — 4 последних 7-дневных окна (от старого к новому).
    - label      = "Неделя 1" .. "Неделя 4"
    - stress / anxiety / depression — среднее по прохождениям внутри окна (0.0 если не было)

    **period=year** — 12 последних календарных месяцев (от старого к новому).
    - label      = "Апр 2025", "Май 2025" и т.д.
    - stress / anxiety / depression — среднее по прохождениям внутри месяца (0.0 если не было)
    """
    if period not in ("week", "month", "year"):
        raise HttpError(422, "period must be 'week', 'month' or 'year'")

    user_id = request.auth["user_id"]
    return UserDassStatisticsService.get_history(user_id=user_id, period=period)
