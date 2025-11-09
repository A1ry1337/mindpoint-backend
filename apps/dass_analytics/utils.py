from datetime import date, timedelta

class DassAnalyticsUtils:

    @staticmethod
    def get_current_and_previous_period_dates(period: str):
        today = date.today()

        if period == "day":
            days = 1
        elif period == "week":
            days = 7
        elif period == "month":
            days = 31
        elif period == "year":
            days = 365
        else:
            raise ValueError("Invalid period")

        # текущий период: последние N дней
        end = today
        start = end - timedelta(days=days - 1)

        # предыдущий период: предыдущие N дней до текущего
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)

        return start, end, prev_start, prev_end

    @staticmethod
    def get_period_dates(period: str, offset: int) -> (date, date):
        """
        Возвращает начало и конец периода с учётом смещения offset (0 — текущий, 1 — предыдущий и т.д.)
        """
        today = date.today()

        if period == "day":
            start = today - timedelta(days=offset)
            end = start
        elif period == "week":
            end = today - timedelta(weeks=offset)
            start = end - timedelta(days=6)
        elif period == "month":
            end = today.replace(day=1) - timedelta(days=offset * 30)
            start = end - timedelta(days=30)
        elif period == "year":
            end = date(today.year - offset, 12, 31)
            start = date(today.year - offset, 1, 1)
        else:
            raise ValueError("Invalid period type")

        return start, end