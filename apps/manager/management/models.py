import uuid
from django.db import models
from django.conf import settings

class Team(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teams"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="member_teams",
        blank=True
    )
    team_leads = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="leading_teams",
        through="TeamLead",
        blank=True
    )

    def __str__(self):
        return f"{self.name} (manager={self.manager.username})"

class TeamLead(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("team", "user")
