from ninja import Router, Query
from typing import List, Optional
from datetime import date

from .models import Dass9Result
from .schemas import Dass9Input, Dass9Output, QuestionOutput
from .services import Dass9Service
from ...auth_user.models import User
from ...auth_user.permissions import JWTAuth

router = Router(tags=["Dass assessments(Тестирование по методике Dass)"])

@router.post("/", auth=JWTAuth())
def save_dass9_result(request, payload: Dass9Input):
    """
    Сохранить результат DASS-9 для текущего пользователя
    """
    userInfo = request.auth
    result = Dass9Service.save_result(
        userInfo=userInfo,
        depression=payload.depression,
        stress=payload.stress,
        anxiety=payload.anxiety,
    )

    if result is None:
        return {"message": "Вы уже проходили тест сегодня!"}

    return ({
        "date": result.date,
        "depression": result.depression_score,
        "stress": result.stress_score,
        "anxiety": result.anxiety_score
    })

@router.get("/check", auth=JWTAuth())
def check_dass9_passed_today(request):
    """
    Проверка: проходил ли пользователь DASS-9 сегодня
    """
    user_id = request.auth["user_id"]
    passed = Dass9Result.objects.filter(user_id=user_id, date=date.today()).exists()
    return {"passed_today": passed}


@router.get("/", response=List[Dass9Output], auth=JWTAuth())
def get_dass9_result(
        request,
        from_date: Optional[date] = Query(None),
        to_date: Optional[date] = Query(None)
):
    """
    Получить историю результатов текущего пользователя
    с возможностью фильтрации по диапазону дат
    """

    user_id = request.auth["user_id"]
    results = Dass9Service.get_results(user_id=user_id, from_date=from_date, to_date=to_date)

    return [
        {
            "date": r.date,
            "depression": r.depression_score,
            "stress": r.stress_score,
            "anxiety": r.anxiety_score,
        }
        for r in results
    ]

@router.get("/random", response=List[QuestionOutput])
def get_dass9_questions(request):
    """
    Получить 9 случайных вопросов (по 3 на каждую тему)
    """
    questions = Dass9Service.get_random_questions()
    return [
        {
            "id": q.id,
            "text": q.text,
            "type": q.type,
            "answers": Dass9Service.ANSWERS_MAP
        }
        for q in questions
    ]
