from datetime import date
from typing import Optional
from ninja import Router, Query
from apps.auth_user.permissions import JWTAuthManager
from apps.dass_analytics.services import StatisticsService
from apps.dass_analytics.schemas import IpsStatisticsOut

router = Router(tags=["Аналитика DASS"])

@router.get("/ips", response=IpsStatisticsOut, auth=JWTAuthManager())
def get_ips_statistics(
        request,
        period: Optional[str] = Query("day", description="day | week | month | year")
):
    """
    Возвращает статистику IPS (психоэмоциональное состояние)
    с динамикой изменения за предыдущий период.
    """
    manager_id = request.auth["user_id"]
    return StatisticsService.get_ips_statistics(manager_id, period=period)
