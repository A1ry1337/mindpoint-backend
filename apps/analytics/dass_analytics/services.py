from typing import Dict, Optional, List
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from datetime import date, timedelta

from apps.assessments.dass.models import Dass9Result
from apps.auth_user.models import User
from apps.analytics.dass_analytics.utils import DassAnalyticsUtils
from apps.manager.management.models import Team


class StatisticsService:

    @staticmethod
    def _calc_change(old_value: float, new_value: float) -> Dict:
        if old_value == 0:
            return {"direction": "up" if new_value > 0 else "neutral", "percent": None}
        diff = new_value - old_value
        percent = abs((diff / old_value) * 100)
        if diff > 0:
            direction = "up"
        elif diff < 0:
            direction = "down"
        else:
            direction = "neutral"
        return {"direction": direction, "percent": round(percent, 2)}

    @staticmethod
    def get_ips_overview(manager_id: str,
                              team_id: Optional[str] = None,
                              period: str = "day") -> Dict[str, any]:
        start, end, prev_start, prev_end = DassAnalyticsUtils.get_current_and_previous_period_dates(period)

        if team_id:
            team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
            member_ids = team.members.values_list("id", flat=True)
        else:
            member_ids = User.objects.filter(manager_id=manager_id).values_list("id", flat=True)

        # Текущий и предыдущий периоды
        qs = Dass9Result.objects.filter(user_id__in=member_ids, date__range=[start, end])
        prev_qs = Dass9Result.objects.filter(user_id__in=member_ids, date__range=[prev_start, prev_end])

        # Средние значения
        curr_avg = qs.aggregate(
            avg_anxiety=Avg("anxiety_score"),
            avg_depression=Avg("depression_score"),
            avg_stress=Avg("stress_score")
        )
        prev_avg = prev_qs.aggregate(
            avg_anxiety=Avg("anxiety_score"),
            avg_depression=Avg("depression_score"),
            avg_stress=Avg("stress_score")
        )

        def safe_value(val): return val or 0.0

        curr_anxiety = safe_value(curr_avg["avg_anxiety"])
        curr_depression = safe_value(curr_avg["avg_depression"])
        curr_stress = safe_value(curr_avg["avg_stress"])
        prev_anxiety = safe_value(prev_avg["avg_anxiety"])
        prev_depression = safe_value(prev_avg["avg_depression"])
        prev_stress = safe_value(prev_avg["avg_stress"])

        curr_ips_raw = (curr_anxiety + curr_depression + curr_stress) / 3 if any([curr_anxiety, curr_depression, curr_stress]) else 0
        prev_ips_raw = (prev_anxiety + prev_depression + prev_stress) / 3 if any([prev_anxiety, prev_depression, prev_stress]) else 0

        curr_ips = 100 - (curr_ips_raw / 27) * 100 if curr_ips_raw != 0 else 0
        prev_ips = 100 - (prev_ips_raw / 27) * 100 if prev_ips_raw != 0 else 0

        stats = [
            {
                "type": "ips",
                "score": round(curr_ips, 2),
                "max_score": 100.0,
                "change": StatisticsService._calc_change(prev_ips, curr_ips)
            },
            {
                "type": "anxiety",
                "score": round(curr_anxiety, 2),
                "max_score": 9.0,
                "change": StatisticsService._calc_change(prev_anxiety, curr_anxiety)
            },
            {
                "type": "depression",
                "score": round(curr_depression, 2),
                "max_score": 9.0,
                "change": StatisticsService._calc_change(prev_depression, curr_depression)
            },
            {
                "type": "stress",
                "score": round(curr_stress, 2),
                "max_score": 9.0,
                "change": StatisticsService._calc_change(prev_stress, curr_stress)
            },
        ]

        return {
            "period": period,
            "statistics": stats
        }

    @staticmethod
    def get_test_count(manager_id: str,
                       team_id: str,
                       period: str = "week") -> Dict[str, any]:
        """
        Возвращает количество прохождений теста DASS9 за последние 4 периода
        (дня, недели, месяца или года) для выбранной команды.
        Если данных нет — добавляется сообщение.
        """
        team = get_object_or_404(Team, id=team_id, manager_id=manager_id)
        member_ids = team.members.values_list("id", flat=True)

        periods: List[Dict] = []

        for offset in range(4):
            start, end = DassAnalyticsUtils.get_period_dates(period, offset)
            count = Dass9Result.objects.filter(
                user_id__in=member_ids,
                date__range=[start, end]
            ).count()

            entry = {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "test_count": count,
            }

            if count == 0:
                entry["message"] = "Данные ещё не собраны"

            periods.append(entry)

        # Сортируем по возрастанию (от старого к новому)
        periods.reverse()

        return {"period": period, "periods": periods}

    @staticmethod
    def get_teams_test_comparison(manager_id: str,
                                  period: str = "week",
                                  team_ids: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Возвращает количество прохождений теста DASS9 по всем (или выбранным) командам
        за текущий и предыдущий периоды, с процентом изменения.
        """
        teams_qs = Team.objects.filter(manager_id=manager_id)
        if team_ids:
            teams_qs = teams_qs.filter(id__in=team_ids)

        teams = list(teams_qs)
        start, end, prev_start, prev_end = DassAnalyticsUtils.get_current_and_previous_period_dates(period)

        results = []

        for team in teams:
            member_ids = team.members.values_list("id", flat=True)

            curr_count = Dass9Result.objects.filter(
                user_id__in=member_ids, date__range=[start, end]
            ).count()
            prev_count = Dass9Result.objects.filter(
                user_id__in=member_ids, date__range=[prev_start, prev_end]
            ).count()

            # Вычисляем направление и процент
            if prev_count == 0:
                direction = "up" if curr_count > 0 else "neutral"
                percent = None
            else:
                diff = curr_count - prev_count
                direction = "up" if diff > 0 else "down" if diff < 0 else "neutral"
                percent = abs(diff / prev_count * 100)

            results.append({
                "team_id": str(team.id),
                "team_name": team.name,
                "current_count": curr_count,
                "previous_count": prev_count,
                "change": {
                    "direction": direction,
                    "percent": round(percent, 2) if percent is not None else None
                }
            })

        return {
            "period": period,
            "teams": results
        }

    @staticmethod
    def get_risk_percent_by_categories(
            manager_id: str,
            team_ids: Optional[List[str]] = None,
            period: str = "day"
    ) -> Dict[str, any]:
        """
        Возвращает процент сотрудников в зоне риска по категориям
        для всех или выбранных команд за указанный период.
        """
        # Определяем дату начала периода
        today = date.today()
        days_map = {"day": 1, "week": 7, "month": 31, "year": 365}
        days = days_map.get(period, 1)
        start_date = today - timedelta(days=days - 1)
        end_date = today

        teams_qs = Team.objects.filter(manager_id=manager_id)
        if team_ids:
            teams_qs = teams_qs.filter(id__in=team_ids)

        results = []

        for team in teams_qs:
            member_ids = list(team.members.values_list("id", flat=True))
            total_members = len(member_ids)

            if total_members == 0:
                results.append({
                    "team_id": str(team.id),
                    "team_name": team.name,
                    "total_members": 0,
                    "depression": {"risk_members": 0, "risk_percent": None},
                    "anxiety": {"risk_members": 0, "risk_percent": None},
                    "stress": {"risk_members": 0, "risk_percent": None},
                })
                continue

            # ---- ДЕПРЕССИЯ >= 5 ----
            dep_members = Dass9Result.objects.filter(
                user_id__in=member_ids,
                depression_score__gte=5,
                date__range=[start_date, end_date]
            ).values_list("user_id", flat=True).distinct().count()
            dep_percent = round(dep_members / total_members * 100, 2) if total_members else None

            # ---- ТРЕВОГА >= 4 ----
            anx_members = Dass9Result.objects.filter(
                user_id__in=member_ids,
                anxiety_score__gte=4,
                date__range=[start_date, end_date]
            ).values_list("user_id", flat=True).distinct().count()
            anx_percent = round(anx_members / total_members * 100, 2) if total_members else None

            # ---- СТРЕСС >= 5 ----
            str_members = Dass9Result.objects.filter(
                user_id__in=member_ids,
                stress_score__gte=5,
                date__range=[start_date, end_date]
            ).values_list("user_id", flat=True).distinct().count()
            str_percent = round(str_members / total_members * 100, 2) if total_members else None

            results.append({
                "team_id": str(team.id),
                "team_name": team.name,
                "total_members": total_members,
                "depression": {"risk_members": dep_members, "risk_percent": dep_percent},
                "anxiety": {"risk_members": anx_members, "risk_percent": anx_percent},
                "stress": {"risk_members": str_members, "risk_percent": str_percent},
            })

        return {"teams": results}

    @staticmethod
    def get_severity_distribution_by_team(
            manager_id: str,
            team_ids: Optional[List[str]] = None,
            period: str = "day"
    ) -> Dict[str, any]:
        """
        Возвращает распределение сотрудников по уровню выраженности
        (нормальный, лёгкий, средний, высокий, очень высокий)
        депрессии, тревожности и стресса для выбранных команд
        """
        from django.db.models import Avg

        # Определяем период
        today = date.today()
        period_days = {"day": 1, "week": 7, "month": 31, "year": 365}
        days = period_days.get(period, 1)
        start_date = today - timedelta(days=days - 1)

        # Получаем команды менеджера
        teams = Team.objects.filter(manager_id=manager_id)
        if team_ids:
            teams = teams.filter(id__in=team_ids)

        # Уровни тяжести
        SEVERITY_LEVELS = {
            "depression": [
                ("Normal", 0, 2),
                ("Mild", 3, 3),
                ("Moderate", 4, 4),
                ("High", 5, 6),
                ("Very_High", 7, 9),
            ],
            "anxiety": [
                ("Normal", 0, 1),
                ("Mild", 2, 2),
                ("Moderate", 3, 3),
                ("High", 4, 5),
                ("Very_High", 6, 9),
            ],
            "stress": [
                ("Normal", 0, 2),
                ("Mild", 3, 3),
                ("Moderate", 4, 4),
                ("High", 5, 6),
                ("Very_High", 7, 9),
            ]
        }

        results = []

        for team in teams:
            # Получаем участников команды
            members = list(team.members.all())
            member_ids = [member.id for member in members]
            total_members = len(members)

            # Базовая структура для команды
            team_data = {
                "team_id": str(team.id),
                "team_name": team.name,
                "total_members": total_members,
                "depression": {},
                "anxiety": {},
                "stress": {},
            }

            if total_members == 0:
                # Если нет участников, заполняем нулями
                for metric in SEVERITY_LEVELS:
                    for level_name, _, _ in SEVERITY_LEVELS[metric]:
                        team_data[metric][level_name] = {
                            "members": 0,
                            "percent": 0.0
                        }
                results.append(team_data)
                continue

            # Получаем средние баллы ВСЕХ участников за период
            # Используем один запрос для всех показателей
            user_scores_query = Dass9Result.objects.filter(
                user_id__in=member_ids,
                date__gte=start_date,
                date__lte=today
            ).values('user_id').annotate(
                avg_depression=Avg('depression_score'),
                avg_anxiety=Avg('anxiety_score'),
                avg_stress=Avg('stress_score')
            )

            # Создаем словарь для хранения средних баллов
            # Инициализируем всех участников как None (нет данных)
            member_scores = {
                user_id: {
                    "depression": None,
                    "anxiety": None,
                    "stress": None
                }
                for user_id in member_ids
            }

            # Заполняем данные для тех, у кого есть результаты
            for row in user_scores_query:
                user_id = row['user_id']
                member_scores[user_id] = {
                    "depression": row['avg_depression'],
                    "anxiety": row['avg_anxiety'],
                    "stress": row['avg_stress']
                }

            # Для каждого показателя считаем распределение
            for metric in ["depression", "anxiety", "stress"]:
                # Инициализируем счетчики для всех уровней
                level_counts = {level[0]: 0 for level in SEVERITY_LEVELS[metric]}

                # Считаем участников по уровням
                for user_id in member_ids:
                    score = member_scores[user_id][metric]

                    # Пропускаем если нет данных
                    if score is None:
                        continue

                    # Округляем средний балл до целого
                    rounded_score = round(score)

                    # Определяем уровень
                    for level_name, min_score, max_score in SEVERITY_LEVELS[metric]:
                        if min_score <= rounded_score <= max_score:
                            level_counts[level_name] += 1
                            break

                # Заполняем результат для показателя
                for level_name, _, _ in SEVERITY_LEVELS[metric]:
                    count = level_counts[level_name]
                    percent = round((count / total_members) * 100, 2) if total_members > 0 else 0.0

                    team_data[metric][level_name] = {
                        "members": count,
                        "percent": percent
                    }

            results.append(team_data)

        return {"teams": results}

    @staticmethod
    def get_periodic_test_counts(manager_id: str, team_ids: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Возвращает ОБЩЕЕ количество прохождений теста DASS9 за периоды:
        - week (последние 7 дней),
        - month (последние 31 день),
        - year (последние 365 дней)

        Для всех команд менеджера или только для указанных team_ids.
        """
        teams_qs = Team.objects.filter(manager_id=manager_id)
        if team_ids:
            teams_qs = teams_qs.filter(id__in=team_ids)

        # Собираем ВСЕ ID участников по всем командам
        all_member_ids = set()
        for team in teams_qs:
            all_member_ids.update(team.members.values_list("id", flat=True))

        if not all_member_ids:
            return {
                "counts": {
                    "week": 0,
                    "month": 0,
                    "year": 0
                }
            }

        today = date.today()
        periods = {
            "week": (today - timedelta(days=6), today),
            "month": (today - timedelta(days=30), today),
            "year": (today - timedelta(days=364), today),
        }

        counts = {}
        for period_name, (start, end) in periods.items():
            cnt = Dass9Result.objects.filter(
                user_id__in=all_member_ids,
                date__range=[start, end]
            ).count()
            counts[period_name] = cnt

        return {"counts": counts}