from calendar import monthrange
from datetime import date, timedelta
from typing import List


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
        if period == "week":
            end = today - timedelta(weeks=offset)
            start = end - timedelta(days=6)
            count_days = 7 * 4
        elif period == "month":
            end = today.replace(day=1) - timedelta(days=offset * 30)
            start = end - timedelta(days=30)
            count_days = 30 * 4
        elif period == "year":
            end = date(today.year - offset, 12, 31)
            start = date(today.year - offset, 1, 1)
            count_days = 365 * 4
        else:
            raise ValueError("Invalid period type")

        return start, end, count_days

    @staticmethod
    def get_intervals_with_labels(period: str) -> list[tuple[date, date, str]]:
        today = date.today()

        if period == "week":
            intervals = []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                label = d.strftime("%d %b")
                intervals.append((d, d, label))
            return intervals

        elif period == "month":
            intervals = []
            for i in range(3, -1, -1):
                end = today - timedelta(days=7 * i)
                start = end - timedelta(days=6)
                label = f"{start.strftime('%d')}–{end.strftime('%d %b')}"
                intervals.append((start, end, label))
            return intervals

        elif period == "year":
            intervals = []
            for i in range(11, -1, -1):
                if i == 0:
                    year = today.year
                    month = today.month
                    start = date(year, month, 1)
                    end = today
                else:
                    month_offset = today.month - i
                    if month_offset <= 0:
                        year = today.year - 1
                        month = 12 + month_offset
                    else:
                        year = today.year
                        month = month_offset
                    _, last_day = monthrange(year, month)
                    start = date(year, month, 1)
                    end = date(year, month, last_day)
                label = start.strftime("%b %Y")
                intervals.append((start, end, label))
            return intervals

        else:
            raise ValueError("period must be 'week', 'month', or 'year'")