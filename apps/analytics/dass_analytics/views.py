from ninja import Router, Query
from typing import Optional
from apps.auth_user.permissions import JWTAuthManager
from apps.analytics.dass_analytics.services import StatisticsService
from apps.analytics.dass_analytics.schemas import MentalStatisticsOut, TestCountOut, TeamsTestComparisonOut, \
    TeamsTestComparisonIn, RiskTeamsOut, RiskTeamsIn, SeverityTeamsIn, SeverityTeamsOut

router = Router(tags=["Аналитика DASS"])

@router.get("/ips_overview", response=MentalStatisticsOut, auth=JWTAuthManager())
def get_mental_statistics(
        request,
        period: Optional[str] = Query("day", description="day | week | month | year")
):
    """
    Возвращает статистику IPS, тревожности, депрессии и стресса
    с динамикой изменения за предыдущий период.
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_ips_overview(manager_id, period=period)

@router.get("/test_count", response=TestCountOut, auth=JWTAuthManager())
def get_test_count(
        request,
        period: Optional[str] = Query("week", description="day | week | month | year"),
        team_id: str = Query(..., description="ID команды (обязательно)")
):
    """
    Возвращает количество прохождений теста DASS9 за последние 4 периода
    (дня, недели, месяца или года) для выбранной команды.
    Если в периоде нет данных — добавляется сообщение "Данные ещё не собраны".
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_test_count(manager_id, team_id=team_id, period=period)

@router.post("/test_count_common", response=TeamsTestComparisonOut, auth=JWTAuthManager())
def get_teams_test_comparison(request, payload: TeamsTestComparisonIn):
    """
    Возвращает количество прохождений теста DASS9 для всех (или выбранных) команд
    за указанный период и предыдущий, с динамикой изменения.
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_teams_test_comparison(
        manager_id,
        period=payload.period,
        team_ids=payload.team_ids
    )

@router.post("/risk_categories", response=RiskTeamsOut, auth=JWTAuthManager())
def get_risk_categories(request, payload: RiskTeamsIn):
    """
    Возвращает процент сотрудников в зоне риска по категориям
    (депрессия, тревога, стресс) по выбранным или всем командам
    с учётом периода: day, week, month, year.
    """
    manager_id = request.auth["user_id"]

    return StatisticsService.get_risk_percent_by_categories(
        manager_id=manager_id,
        team_ids=payload.team_ids,
        period=payload.period
    )


@router.post("/severity_distribution", response= SeverityTeamsOut, auth=JWTAuthManager())
def get_severity_distribution(request, payload: SeverityTeamsIn):
    """
    Возвращает распределение сотрудников по уровням тяжести
    (Normal, Mild, Moderate, High, Very High) для депрессии, тревоги и стресса
    для выбранных команд или всех команд менеджера.

    Параметры:
    - team_ids: список ID команд (если не указан, берутся все команды менеджера)
    - period: период для расчета статистики ('day', 'week', 'month', 'year')

    Ответ содержит количество участников и процент для каждого уровня тяжести
    по каждой метрике (depression, anxiety, stress) для каждой команды.
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_severity_distribution_by_team(
        manager_id=manager_id,
        team_ids=payload.team_ids,
        period=payload.period
    )