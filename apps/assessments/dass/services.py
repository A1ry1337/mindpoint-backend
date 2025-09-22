from datetime import date
from typing import Optional, List

from django.db import models
from .models import Dass9Result, Question
import random

from ...auth_user.models import User


class Dass9Service:

    ANSWERS_MAP = {
        0: "Совсем не было",
        1: "Немного, иногда",
        2: "Часто, значительную часть времени",
        3: "Почти всё время",
    }

    @staticmethod
    def save_result(userInfo, depression: int, stress: int, anxiety: int):
        user = User.objects.get(id=userInfo["user_id"])
        today = date.today()

        existing = Dass9Result.objects.filter(user=user, date=today).first()
        if existing:
            return None

        result = Dass9Result.objects.create(
            user=user,
            date=today,
            depression_score=depression,
            stress_score=stress,
            anxiety_score=anxiety,
        )
        return result

    @staticmethod
    def get_random_questions():
        """
        Возвращает 9 вопросов: по 3 из каждой категории
        """
        result = {}
        questions = []

        for q_type in Question.QuestionType:
            qs = list(Question.objects.filter(type=q_type))
            selected = random.sample(qs, min(3, len(qs)))
            questions.extend(selected)
            result[q_type.label] = [q.text for q in selected]

        return questions

    @staticmethod
    def get_results(user_id: int, from_date: Optional[date] = None, to_date: Optional[date] = None) -> List[Dass9Result]:
        """
        Получить результаты DASS-9 для пользователя с фильтрацией по датам
        """
        user = User.objects.get(id=user_id)
        results = Dass9Result.objects.filter(user=user)

        if from_date:
            results = results.filter(date__gte=from_date)
        if to_date:
            results = results.filter(date__lte=to_date)

        return results.order_by("-date")
