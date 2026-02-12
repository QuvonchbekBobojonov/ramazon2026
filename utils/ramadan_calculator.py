
from datetime import datetime, timedelta
from .ramadan_data import ramadan_data

def get_region_offset(region_slug):
    return ramadan_data["regional_offsets"].get(region_slug, 0)

def calculate_time(time_str, offset_minutes):
    if not time_str:
        return None
    time_format = "%H:%M"
    t = datetime.strptime(time_str, time_format)
    new_time = t + timedelta(minutes=offset_minutes)
    return new_time.strftime(time_format)

def get_daily_times(date_str, region_slug="tashkent"):
    offset = get_region_offset(region_slug)
    for day in ramadan_data["calendar"]:
        if day["date"] == date_str:
            suhoor = calculate_time(day.get("suhoor"), offset)
            iftar = calculate_time(day.get("iftar"), offset)
            return {
                "day": day["day"],
                "date": format_date_uz(day["date"]),
                "weekday": day["weekday"],
                "suhoor": suhoor,
                "iftar": iftar,
                "note": day.get("note"),
                "region": region_slug,
                "offset": offset
            }
    return None

def get_today_times(region_slug="tashkent"):
    today_str = datetime.now().strftime("%Y-%m-%d")
    return get_daily_times(today_str, region_slug)

def get_tomorrow_times(region_slug="tashkent"):
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    return get_daily_times(tomorrow_str, region_slug)


MONTH_MAP = {
    1: "Yanvar", 2: "Fevral", 3: "Mart", 4: "Aprel", 5: "May", 6: "Iyun",
    7: "Iyul", 8: "Avgust", 9: "Sentabr", 10: "Oktabr", 11: "Noyabr", 12: "Dekabr"
}

def format_date_uz(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.day}-{MONTH_MAP[dt.month]}"

def get_full_calendar(region_slug="tashkent"):
    offset = get_region_offset(region_slug)
    today_str = datetime.now().strftime("%Y-%m-%d")
    calendar_list = []
    
    for day in ramadan_data["calendar"]:
        suhoor = calculate_time(day.get("suhoor"), offset)
        iftar = calculate_time(day.get("iftar"), offset)
        calendar_list.append({
            "day": day["day"],
            "date": format_date_uz(day["date"]),
            "weekday": day["weekday"],
            "suhoor": suhoor,
            "iftar": iftar,
            "note": day.get("note"),
            "region": region_slug,
            "is_today": day["date"] == today_str
        })
    return calendar_list
