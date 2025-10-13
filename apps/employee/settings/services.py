from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from .models import ManagerAssignmentRequest
from apps.auth_user.models import User

class ManagerAssignmentService:

    @staticmethod
    def create_request_by_name(user_id: str, manager_username: str):
        user = get_object_or_404(User, id=user_id)

        try:
            manager = User.objects.get(username=manager_username, is_manager=True)
        except User.DoesNotExist:
            raise HttpError(404, "Менеджер с таким именем не найден")

        if user.manager_id == manager.id:
            raise HttpError(400, "Менеджер уже закреплён за пользователем")

        # Проверяем, есть ли уже pending-запрос к этому менеджеру
        existing_request = ManagerAssignmentRequest.objects.filter(
            user=user,
            manager=manager,
            is_approved__isnull=True  # pending
        ).first()

        if existing_request:
            raise HttpError(400, "Уже существует pending-запрос к этому менеджеру")

        request = ManagerAssignmentRequest.objects.create(
            user=user,
            manager=manager,
            is_approved=None
        )

        status = "pending" if request.is_approved is None else ("approved" if request.is_approved else "rejected")

        return {
            "request_id": request.id,
            "manager_username": request.manager.username,
            "status": status,
            "created_at": request.created_at.isoformat()
        }

    @staticmethod
    def list_requests(user_id: str):
        requests = ManagerAssignmentRequest.objects.filter(user_id=user_id).select_related("manager")
        result = []

        for r in requests:
            if r.is_approved is None:
                status = "pending"
            elif r.is_approved:
                status = "approved"
            else:
                status = "rejected"

            result.append({
                "request_id": r.id,
                "manager_username": r.manager.username,
                "status": status,
                "created_at": r.created_at.isoformat()
            })

        return result
