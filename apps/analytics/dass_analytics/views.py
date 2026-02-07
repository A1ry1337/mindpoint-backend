from ninja import Router, Query
from typing import Optional
from apps.auth_user.permissions import JWTAuthManager, JWTAuthManagerOrTeamLead
from apps.analytics.dass_analytics.services import StatisticsService
from apps.analytics.dass_analytics.schemas import MentalStatisticsOut, TestCountOut, TeamsTestComparisonOut, \
    TeamsTestComparisonIn, RiskTeamsOut, RiskTeamsIn, SeverityTeamsIn, SeverityTeamsOut, TeamsPeriodicTestCountOut, \
    TeamsPeriodicTestCountIn, PeriodSeverityResponse, PeriodSeverityRequest, TestingCoverageRequest, \
    TestingCoverageResponse

router = Router(tags=["Аналитика DASS"])

@router.get("/ips_overview", response=MentalStatisticsOut, auth=JWTAuthManagerOrTeamLead())
def get_mental_statistics(
        request,
        period: Optional[str] = Query("day", description="day | week | month | year")
):
    """
    Возвращает статистику IPS, тревожности, депрессии и стресса
    с динамикой изменения за предыдущий период.
    """
    manager_id = request.auth["manager_id"]
    is_manager = request.auth["is_manager"]
    user_id = request.auth["user_id"]
    return StatisticsService.get_ips_overview(manager_id, is_manager, user_id, period=period)

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

@router.post("/periodic_test_counts", response=TeamsPeriodicTestCountOut, auth=JWTAuthManager())
def get_periodic_test_counts(request, payload: TeamsPeriodicTestCountIn):
    """
    Возвращает ОБЩЕЕ количество прохождений теста DASS9 за периоды: неделя, месяц, год
    по всем командам менеджера (или по выбранным).
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_periodic_test_counts(manager_id, team_ids=payload.team_ids)

@router.post("/severity_trends", response=PeriodSeverityResponse, auth=JWTAuthManager())
def get_severity_trends(request, payload: PeriodSeverityRequest):
    """
    Возвращает распределение сотрудников по уровням тяжести (Normal, Mild, Moderate, High, Very_High)
    для депрессии, тревоги и стресса с разбивкой по периодам:
    - week → 7 дней (по дням)
    - month → 4 недели (по неделям)
    - year → 12 месяцев (по месяцам)

    Каждый элемент содержит метаинформацию (label, start, end) и 5 уровней с количеством и процентом.
    Если в периоде нет данных — все значения будут 0.
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_severity_trends_by_period(
        manager_id=manager_id,
        team_ids=payload.team_ids,
        period=payload.period
    )

@router.post("/testing_coverage", response=TestingCoverageResponse, auth=JWTAuthManager())
def get_testing_coverage(request, payload: TestingCoverageRequest):
    """
    Возвращает процент покрытия тестированием DASS9 по командам за период:
    - week: последние 7 дней
    - month: последние 31 день
    - year: последние 365 дней

    Процент рассчитывается как:
      (фактические прохождения) / (рабочие дни × участники) × 100

    Рабочие дни = понедельник–пятница.
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_testing_coverage_by_teams(
        manager_id=manager_id,
        team_ids=payload.team_ids,
        period=payload.period
    )