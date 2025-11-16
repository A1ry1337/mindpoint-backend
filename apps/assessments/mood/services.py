from datetime import date
from typing import Optional, List
from .models import MoodResult
from ...auth_user.models import User

class MoodService:

    @staticmethod
    def save_result(user_info, score: int):
        user = User.objects.get(id=user_info["user_id"])
        today = date.today()

        if MoodResult.objects.filter(user=user, date=today).exists():
            return None

        result = MoodResult.objects.create(
            user=user,
            score=score
        )
        return result

    @staticmethod
    def get_results(user_id: int, from_date: Optional[date] = None, to_date: Optional[date] = None) -> List[MoodResult]:
        user = User.objects.get(id=user_id)
        results = MoodResult.objects.filter(user=user)
        if from_date:
            results = results.filter(date__gte=from_date)
        if to_date:
            results = results.filter(date__lte=to_date)
        return results.order_by("-date")
