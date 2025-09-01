from ninja import Router
from typing import List
from django.shortcuts import get_object_or_404

from .models import Dass9Result
from .schemas import Dass9Input, Dass9Output, QuestionOutput
from .services import Dass9Service
from ...auth_user.permissions import JWTAuth

router = Router()

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

    return {
        "date": result.date,
        "depression": result.depression_score,
        "stress": result.stress_score,
        "anxiety": result.anxiety_score
    }


@router.get("/", response=List[Dass9Output])
def list_dass9_results(request):
    """
    Получить историю результатов текущего пользователя
    """
    user =  request.user
    results = Dass9Result.objects.filter(user=user).order_by("-date")
    return [
        {
            "date": r.date,
            "depression": r.depression_score,
            "stress": r.stress_score,
            "anxiety": r.anxiety_score,
            "total": r.total_score,
        }
        for r in results
    ]

@router.get("/random", response=List[QuestionOutput])
def get_random_questions(request):
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
