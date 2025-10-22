from typing import List

from ninja import Router

from apps.auth_user.permissions import JWTAuth
from apps.employee.settings.schemas import ManagerAssignmentRequestOut, ManagerAssignmentRequestByNameIn
from apps.employee.settings.services import ManagerAssignmentService

router = Router(tags=["Настройки пользователя"])

@router.post("/request_manager_by_name", auth=JWTAuth(), response=ManagerAssignmentRequestOut)
def request_manager_by_name(request, data: ManagerAssignmentRequestByNameIn):
    """
    Отправить запрос на привязку к компании по уникальному имени
    """
    user_id = request.auth["user_id"]
    return ManagerAssignmentService.create_request_by_name(user_id, data.manager_username)

@router.get("/my_manager_requests", auth=JWTAuth(), response=List[ManagerAssignmentRequestOut])
def my_manager_requests(request):
    """
    Список всех запросов пользователя с текущим статусом.
    pending - ожидает
    approved - принят
    rejected - отклонён
    """
    user_id = request.auth["user_id"]
    return ManagerAssignmentService.list_requests(user_id)