from ninja import Router, Query
from typing import Optional
from apps.auth_user.permissions import JWTAuthManager
from apps.dass_analytics.services import StatisticsService
from apps.dass_analytics.schemas import MentalStatisticsOut

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
