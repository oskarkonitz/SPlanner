from datetime import datetime, date, timedelta
from storage import load
import math

calendar = {}

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


def plan(data):
    pref_max_per_day = data["settings"].get("max_per_day", 2)
    pref_max_same_subject = data["settings"].get("max_same_subject_per_day", 1)
    today = date.today()

    empty_callendar = callendar_create(data, today)

    # for exam in data["exams"]:
    #     exam_date = date_format(exam["date"])
    #     v_date = exam_date - timedelta(days=1)






data = load()
plan(data)