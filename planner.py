from datetime import datetime, date, timedelta
from storage import load
import math

def date_format(text):
    return datetime.strptime(text, "%Y-%m-%d").date()

def callendar_create(data, tday):
    callendar = {}
    max_date = tday

    for exam in data["exams"]:
        if date_format(exam["date"]) > max_date:
            max_date = date_format(exam["date"])

    while max_date >= tday:
        callendar.update({max_date : []})
        max_date -= timedelta(days=1)

    return callendar

def topics_list_create(data, e_id):
    topics_list = []
    for topic in data["topics"]:
        if topic["exam_id"] == e_id:
            topics_list.append(topic["id"])
    return topics_list

def plan(data):
    pref_max_per_day = data["settings"].get("max_per_day", 2)
    pref_max_same_subject = data["settings"].get("max_same_subject_per_day", 1)
    today = date.today()

    callendar = callendar_create(data, today)

    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        v_date = exam_date - timedelta(days=1)
        t_list = topics_list_create(data, exam["id"])
        t_list.reverse()
        days_available = (v_date - today).days + 1
        needed_daily = math.ceil(len(t_list) / days_available)
        while v_date >= today and len(t_list) > 0:
            for i in range(needed_daily):
                callendar[v_date].append(t_list[0])
                del t_list[0]
            v_date -= timedelta(days=1)

    print(callendar)







data = load()
plan(data)