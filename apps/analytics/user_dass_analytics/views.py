from ninja import Router, Query
from ninja.errors import HttpError

from apps.auth_user.permissions import JWTAuth
from apps.analytics.user_dass_analytics.schemas import (
    UserLastDassResultOut,
    UserDassCompletionStatsOut,
    UserDassHistoryOut,
)
from apps.analytics.user_dass_analytics.services import UserDassStatisticsService


router = Router(tags=["Аналитика DASS пользователя"])


@router.get("/last_result", response=UserLastDassResultOut, auth=JWTAuth())
def get_last_result(request):
    """
    Возвращает последний результат DASS9 для текущего пользователя.

    Для каждой метрики: stress, anxiety, depression возвращается:
    - score: последний балл
    - level: normal | moderate | high
    - change: разница с предыдущим результатом
    - chart: последние значения для графика
    - recommendation_trigger: True, если последний score >= 6

    Если результатов нет, возвращаются дефолтные значения.
    """
    user_id = request.auth["user_id"]
    return UserDassStatisticsService.get_last_result(user_id=user_id)


@router.get("/completion_stats", response=UserDassCompletionStatsOut, auth=JWTAuth())
def get_completion_stats(request):
    """
    Возвращает статистику прохождения теста DASS9.

    - total_tests: общее количество завершённых тестов
    - completion_percent: процент выполнения ожидаемой частоты
    - recommendation_trigger: True, если completion_percent < 30
    """
    user_id = request.auth["user_id"]
    return UserDassStatisticsService.get_completion_stats(user_id=user_id)


@router.get("/history", response=UserDassHistoryOut, auth=JWTAuth())
def get_history(
    request,
    period: str = Query("week", description="week | month | year"),
):
    """
    Возвращает историю DASS9 по актуальным календарным периодам.

    period=week:
    - последние 7 календарных дней, включая сегодня
    - label = дата, например "2026-05-15"
    - start_date = end_date = дата дня

    period=month:
    - последние 4 недели по 7 дней
    - label = "Неделя 1" ... "Неделя 4"

    period=year:
    - последние 12 месяцев
    - label = "Май 2026" и т.д.

    stress / anxiety / depression:
    - для week: среднее значение за день
    - для month: среднее значение за неделю
    - для year: среднее значение за месяц

    Если за период нет результатов, возвращается 0.0.
    """
    if period not in ("week", "month", "year"):
        raise HttpError(422, "period must be 'week', 'month' or 'year'")

    user_id = request.auth["user_id"]
    return UserDassStatisticsService.get_history(user_id=user_id, period=period)