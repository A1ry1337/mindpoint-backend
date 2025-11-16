from ninja import Router, Query
from typing import List, Optional
from datetime import date
from .models import MoodResult
from .schemas import MoodInput, MoodOutput
from .services import MoodService
from ...auth_user.permissions import JWTAuth

router = Router(tags=["Оценка настроения сотрудника"])

@router.post("/", auth=JWTAuth())
def save_mood_result(request, payload: MoodInput):
    """
    Сохранить результат теста настроения текущего пользователя
    """
    user_info = request.auth
    result = MoodService.save_result(user_info, payload.score)
    if result is None:
        return {"message": "Вы уже проходили тест сегодня!"}
    return {"date": result.date, "score": result.score}

@router.get("/check", auth=JWTAuth())
def check_mood_passed_today(request):
    """
    Проверка: проходил ли пользователь тест настроения сегодня
    """
    user_id = request.auth["user_id"]
    passed = MoodResult.objects.filter(user_id=user_id, date=date.today()).exists()
    return {"passed_today": passed}

@router.get("/", response=List[MoodOutput], auth=JWTAuth())
def get_mood_results(request, from_date: Optional[date] = Query(None), to_date: Optional[date] = Query(None)):
    """
    Получить историю результатов теста настроения
    """
    user_id = request.auth["user_id"]
    results = MoodService.get_results(user_id, from_date, to_date)
    return [{"date": r.date, "score": r.score} for r in results]
