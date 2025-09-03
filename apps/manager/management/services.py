from apps.auth_user.models import User


class EmployeeService:
    @staticmethod
    def get_all_employees_by_manager(manager_id):
        employees = User.objects.filter(manager_id=manager_id)
        return [{
            "id": e.id,
            "username": e.username,
            "fullname": e.full_name,
        } for e in employees]
