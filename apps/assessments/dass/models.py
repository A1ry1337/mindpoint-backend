from django.db import models
from django.conf import settings

class Question(models.Model):
    class QuestionType(models.TextChoices):
        DEPRESSION = "depression", "Депрессия"
        STRESS = "stress", "Стресс"
        ANXIETY = "anxiety", "Тревожность"

    text = models.TextField(verbose_name="Текст вопроса")
    type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        verbose_name="Тип вопроса"
    )

    def __str__(self):
        return f"[{self.get_type_display()}] {self.text[:50]}"


class Dass9Result(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dass9_results",
        verbose_name="Сотрудник"
    )
    date = models.DateField(auto_now_add=True, verbose_name="Дата прохождения")
    depression_score = models.PositiveIntegerField(verbose_name="Баллы по депрессии")
    stress_score = models.PositiveIntegerField(verbose_name="Баллы по стрессу")
    anxiety_score = models.PositiveIntegerField(verbose_name="Баллы по тревожности")

    class Meta:
        unique_together = ("user", "date")  # один тест в день
        verbose_name = "Результат DASS-9"
        verbose_name_plural = "Результаты DASS-9"

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.total_score} баллов)"
