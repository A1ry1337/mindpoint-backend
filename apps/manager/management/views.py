from typing import List

from ninja import Router

from apps.auth_user.permissions import JWTAuth
from apps.manager.management.schemas import EmployeeOut
from apps.manager.management.services import EmployeeService

router = Router()

@router.get("/get_all_employees", auth=JWTAuth(), response=List[EmployeeOut])
def get_all_employees(request):
    """
    Получить всех сотрудников по руководителю
    """

    user_id = request.auth["user_id"]

    employees = EmployeeService.get_all_employees_by_manager(user_id)

    return employees