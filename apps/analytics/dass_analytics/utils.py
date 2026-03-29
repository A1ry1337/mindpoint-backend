from calendar import monthrange
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


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
    def get_period_dates(period: str, offset: int):
        today = date.today()

        if period == "week":
            start_of_week = today - timedelta(days=today.weekday())
            start = start_of_week - timedelta(weeks=offset)

            if offset == 0:
                end = today
            else:
                end = start + timedelta(days=6)

            count_days = (end - start).days + 1

        elif period == "month":
            current_month_start = today.replace(day=1)
            start = current_month_start - relativedelta(months=offset)

            if offset == 0:
                end = today
            else:
                end = start + relativedelta(months=1) - timedelta(days=1)

            count_days = (end - start).days + 1

        elif period == "year":
            year = today.year - offset
            start = date(year, 1, 1)

            if offset == 0:
                end = today
            else:
                end = date(year, 12, 31)

            count_days = (end - start).days + 1

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