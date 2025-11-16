from django.db import models
from django.conf import settings

class MoodResult(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mood_results",
        verbose_name="Пользователь"
    )
    date = models.DateField(auto_now_add=True, verbose_name="Дата")
    score = models.PositiveSmallIntegerField(
        verbose_name="Оценка настроения",
        choices=[(i, str(i)) for i in range(1, 6)]  # 1-5
    )

    class Meta:
        unique_together = ("user", "date")  # один тест в день
        verbose_name = "Результат теста настроения"
        verbose_name_plural = "Результаты теста настроения"

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.score})"
