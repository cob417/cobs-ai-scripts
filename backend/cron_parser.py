"""
Cron expression parser with human-readable descriptions
"""

from croniter import croniter
from datetime import datetime, timedelta
import re


# Helper functions for parsing cron fields
def _is_wildcard(s: str) -> bool:
    return s == "*"


def _is_number(s: str) -> bool:
    return s.isdigit()


def _is_range(s: str) -> bool:
    return "-" in s


def _is_list(s: str) -> bool:
    return "," in s


def _is_step(s: str) -> bool:
    return "/" in s


def parse_cron_expression(cron_expr: str) -> dict:
    """
    Parse cron expression and return human-readable description.
    Similar to crontab.guru style descriptions.
    """
    try:
        # Validate and parse cron expression
        cron = croniter(cron_expr, datetime.now())
        
        # Get next 5 run times
        next_runs = []
        base_time = datetime.now()
        for _ in range(5):
            next_time = cron.get_next(datetime)
            next_runs.append(next_time.strftime("%Y-%m-%d %H:%M:%S"))
            base_time = next_time
        
        # Generate human-readable description
        description = _generate_description(cron_expr)
        
        return {
            "cron_expression": cron_expr,
            "description": description,
            "next_runs": next_runs
        }
    except Exception as e:
        raise ValueError(f"Invalid cron expression: {str(e)}")


def _generate_description(cron_expr: str) -> str:
    """Generate human-readable description from cron expression"""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return "Invalid cron expression (must have 5 fields)"
    
    minute, hour, day, month, weekday = parts
    
    # Parse minute
    minute_desc = _parse_minute(minute)
    
    # Parse hour
    hour_desc = _parse_hour(hour)
    
    # Parse day of month
    day_desc = _parse_day(day)
    
    # Parse month
    month_desc = _parse_month(month)
    
    # Parse weekday
    weekday_desc = _parse_weekday(weekday)
    
    # Combine descriptions
    parts_desc = [p for p in [minute_desc, hour_desc, day_desc, month_desc, weekday_desc] if p]
    
    if not parts_desc:
        return "Every minute"
    
    return ", ".join(parts_desc)


def _parse_minute(minute: str) -> str:
    """Parse minute field"""
    if _is_wildcard(minute):
        return None  # Will be handled by hour
    elif _is_number(minute):
        return f"at minute {minute}"
    elif _is_range(minute):
        start, end = minute.split("-")
        return f"minutes {start} through {end}"
    elif _is_list(minute):
        return f"at minutes {minute.replace(',', ', ')}"
    elif _is_step(minute):
        step = minute.split("/")[1]
        return f"every {step} minutes"
    return None


def _parse_hour(hour: str) -> str:
    """Parse hour field"""
    if _is_wildcard(hour):
        return "every hour"
    elif _is_number(hour):
        h = int(hour)
        am_pm = "AM" if h < 12 else "PM"
        h12 = h if h <= 12 else h - 12
        if h == 0:
            h12 = 12
        return f"at {h12}:00 {am_pm}"
    elif _is_range(hour):
        start, end = hour.split("-")
        start_h = int(start)
        end_h = int(end)
        start_ampm = "AM" if start_h < 12 else "PM"
        end_ampm = "AM" if end_h < 12 else "PM"
        start_h12 = start_h if start_h <= 12 else start_h - 12
        end_h12 = end_h if end_h <= 12 else end_h - 12
        if start_h == 0:
            start_h12 = 12
        if end_h == 0:
            end_h12 = 12
        return f"from {start_h12}:00 {start_ampm} to {end_h12}:00 {end_ampm}"
    elif _is_list(hour):
        hours = [int(h) for h in hour.split(",")]
        hour_strs = []
        for h in hours:
            am_pm = "AM" if h < 12 else "PM"
            h12 = h if h <= 12 else h - 12
            if h == 0:
                h12 = 12
            hour_strs.append(f"{h12}:00 {am_pm}")
        return f"at {', '.join(hour_strs)}"
    elif _is_step(hour):
        step = hour.split("/")[1]
        return f"every {step} hours"
    return None


def _parse_day(day: str) -> str:
    """Parse day of month field"""
    if _is_wildcard(day):
        return None
    elif _is_number(day):
        return f"on day {day} of the month"
    elif _is_range(day):
        start, end = day.split("-")
        return f"from day {start} to {end} of the month"
    elif _is_list(day):
        return f"on days {day.replace(',', ', ')} of the month"
    elif _is_step(day):
        step = day.split("/")[1]
        return f"every {step} days"
    return None


def _parse_month(month: str) -> str:
    """Parse month field"""
    month_names = {
        "1": "January", "2": "February", "3": "March", "4": "April",
        "5": "May", "6": "June", "7": "July", "8": "August",
        "9": "September", "10": "October", "11": "November", "12": "December"
    }
    
    if _is_wildcard(month):
        return None
    elif _is_number(month):
        return f"in {month_names.get(month, month)}"
    elif _is_range(month):
        start, end = month.split("-")
        start_name = month_names.get(start, start)
        end_name = month_names.get(end, end)
        return f"from {start_name} to {end_name}"
    elif _is_list(month):
        months = [month_names.get(m, m) for m in month.split(",")]
        return f"in {', '.join(months)}"
    elif _is_step(month):
        step = month.split("/")[1]
        return f"every {step} months"
    return None


def _parse_weekday(weekday: str) -> str:
    """Parse weekday field"""
    day_names = {
        "0": "Sunday", "1": "Monday", "2": "Tuesday", "3": "Wednesday",
        "4": "Thursday", "5": "Friday", "6": "Saturday",
        "7": "Sunday"  # Some systems use 7 for Sunday
    }
    
    if _is_wildcard(weekday):
        return None
    elif _is_number(weekday):
        return f"on {day_names.get(weekday, weekday)}"
    elif _is_range(weekday):
        start, end = weekday.split("-")
        start_name = day_names.get(start, start)
        end_name = day_names.get(end, end)
        return f"from {start_name} to {end_name}"
    elif _is_list(weekday):
        days = [day_names.get(d, d) for d in weekday.split(",")]
        return f"on {', '.join(days)}"
    elif _is_step(weekday):
        step = weekday.split("/")[1]
        return f"every {step} weekdays"
    return None
