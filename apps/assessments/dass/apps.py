from django.apps import AppConfig
from psycopg import OperationalError


class DassConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assessments.dass'

    # def ready(self):
    #     from .models import Question
    #     try:
    #         if Question.objects.count() == 0:
    #             Question.objects.bulk_create([
    #                 Question(type=Question.QuestionType.DEPRESSION,
    #                          text="Мне трудно испытывать какие-либо положительные эмоции"),
    #                 Question(type=Question.QuestionType.DEPRESSION,
    #                          text="Мне трудно быть инициативным (проявлять инициативу) чтобы что-либо делать"),
    #                 Question(type=Question.QuestionType.DEPRESSION,
    #                          text="Я чувствую, что мне нечего ждать от будущего"),
    #                 Question(type=Question.QuestionType.DEPRESSION, text="Я чувствую уныние и хандру"),
    #                 Question(type=Question.QuestionType.DEPRESSION, text="Мне трудно испытывать энтузиазм к чему-либо"),
    #                 Question(type=Question.QuestionType.DEPRESSION, text="Я чувствую себя никчемным человеком"),
    #                 Question(type=Question.QuestionType.DEPRESSION, text="Мне кажется, что жизнь не имеет смысла"),
    #
    #                 Question(type=Question.QuestionType.ANXIETY, text="Я чувствую сухость во рту"),
    #                 Question(type=Question.QuestionType.ANXIETY,
    #                          text="Я испытываю затруднение дыхания (например, чрезмерно быстрое дыхание, одышка при отсутствии физических нагрузок)"),
    #                 Question(type=Question.QuestionType.ANXIETY, text="Я испытываю дрожь в теле (например, в руках)"),
    #                 Question(type=Question.QuestionType.ANXIETY,
    #                          text="Я избегаю ситуаций, в которых могу оказаться некомпетентным и выставить себя дураком"),
    #                 Question(type=Question.QuestionType.ANXIETY, text="Я чувствую, что бываю близок к панике"),
    #                 Question(type=Question.QuestionType.ANXIETY,
    #                          text="Я чувствую сердечную деятельность в отсутствие физической нагрузки"),
    #                 Question(type=Question.QuestionType.ANXIETY,
    #                          text="Я чувствую страх без какой-либо уважительной причины"),
    #
    #                 Question(type=Question.QuestionType.STRESS, text="Мне трудно отвлечься, развеяться"),
    #                 Question(type=Question.QuestionType.STRESS, text="Я слишком остро реагирую на ситуации"),
    #                 Question(type=Question.QuestionType.STRESS, text="Я чувствую, что использую много нервной энергии"),
    #                 Question(type=Question.QuestionType.STRESS, text="Я чувствую себя взволнованным"),
    #                 Question(type=Question.QuestionType.STRESS, text="Мне трудно расслабиться"),
    #                 Question(type=Question.QuestionType.STRESS,
    #                          text="Я легко раздражаюсь, если меня отвлекают от работы"),
    #                 Question(type=Question.QuestionType.STRESS, text="Я довольно обидчив"),
    #             ])
    #     except OperationalError:
    #         pass
