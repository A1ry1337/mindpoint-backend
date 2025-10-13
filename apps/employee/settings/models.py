import uuid
from django.db import models
from django.conf import settings

class ManagerAssignmentRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="manager_requests")
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_requests")
    is_approved = models.BooleanField(null=True)  # None - ожидает, True - подтверждено, False - отклонено
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "manager_assignment_request"
        unique_together = ("user", "manager")
