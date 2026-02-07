from ninja import Router

from apps.analytics.mood_analytics.schemas import TeamsMoodResponseOut, TeamsMoodRequestIn, \
    TeamsMoodDistributionResponseOut, TeamsMoodDistributionRequestIn
from apps.analytics.mood_analytics.services import MoodStatisticsService
from apps.auth_user.permissions import JWTAuthManagerOrTeamLead

router = Router(tags=["Аналитика настроения"])


@router.post("/teams_mood", response=TeamsMoodResponseOut, auth=JWTAuthManagerOrTeamLead())
def get_teams_mood(request, payload: TeamsMoodRequestIn):
    """
    Возвращает статистику настроения (1–5) по командам менеджера.

    Параметры:
    - period: "week" | "month" | "year"
        week  -> 7 дней (по дням)
        month -> 4 недели (текущая и три предыдущие)
        year  -> 12 месяцев (по месяцам)
    - team_id (опционально): если задано — только эта команда,
      если нет — все команды менеджера.
    """
    manager_id = request.auth["manager_id"]
    is_manager = request.auth["is_manager"]
    user_id = request.auth["user_id"]

    return MoodStatisticsService.get_teams_mood(
        is_manager=is_manager,
        user_id=user_id,
        manager_id=manager_id,
        period=payload.period,
        team_id=payload.team_id,
    )

@router.post(
    "/teams_mood_distribution",
    response=TeamsMoodDistributionResponseOut,
    auth=JWTAuthManagerOrTeamLead(),
)
def get_teams_mood_distribution(request, payload: TeamsMoodDistributionRequestIn):
    """
    Возвращает процентное распределение настроения (1–5)
    по периодам времени.

    - period: day | week | month | year
    - team_ids:
        - если переданы → считаем по ним
        - если нет → считаем по всем командам менеджера
    """

    manager_id = request.auth["manager_id"]
    is_manager = request.auth["is_manager"]
    user_id = request.auth["user_id"]

    return MoodStatisticsService.get_mood_distribution(
        is_manager=is_manager,
        manager_id=manager_id,
        user_id=user_id,
        period=payload.period,
        team_ids=payload.team_ids,
    )
