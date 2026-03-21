from ninja import Router
from apps.auth_user.permissions import JWTAuth
from apps.analytics.user_dass_analytics.schemas import UserLastDassResultOut
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