from datetime import datetime, timedelta
import calendar

def interpret_date_range(text):
    today = datetime.now().date()

    text = text.lower()

    if "hoje" in text:
        return today.isoformat(), today.isoformat()
    elif "ontem" in text:
        yesterday = today - timedelta(days=1)
        return yesterday.isoformat(), yesterday.isoformat()
    elif "esta semana" in text or "nesta semana" in text:
        start = today - timedelta(days=today.weekday())  # Monday
        return start.isoformat(), today.isoformat()
    elif "este mês" in text or "neste mês" in text:
        start = today.replace(day=1)
        return start.isoformat(), today.isoformat()
    else:
        # Check for specific month by name
        months = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }
        for month_name, number in months.items():
            if month_name in text:
                year = today.year
                start = datetime(year, number, 1).date()
                end = datetime(year, number, calendar.monthrange(year, number)[1]).date()
                return start.isoformat(), end.isoformat()

    return None, None  # not recognized
