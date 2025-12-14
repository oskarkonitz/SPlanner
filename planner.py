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

    for exam in data["exams"]:
        callendar.update({date_format(exam["date"]): ["E"]})

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
        e_date = exam_date - timedelta(days=1)

        border_day = e_date
        while "E" not in callendar[border_day] and border_day != today:
            border_day -= timedelta(days=1)

        t_list = topics_list_create(data, exam["id"])
        # t_list.reverse()

        days_available = (e_date - border_day).days + 1
        needed_daily = math.ceil(len(t_list) / days_available)
        tasks_remaining = len(t_list)

        if needed_daily == 1:
            border_day = e_date - timedelta(days=(tasks_remaining))
        else:
            border_day -= timedelta(days=1)

        if border_day == today:
            border_day -= timedelta(days=1)

        while border_day <= e_date:
            for i in range(needed_daily):
                if len(t_list) > 0:
                    callendar[border_day + timedelta(days=1)].append(t_list[0])
                    del t_list[0]
                    tasks_remaining -= 1
            border_day += timedelta(days=1)

    for topic in data["topics"]:
        for key, value in callendar.items():
            if topic["id"] in value:
                topic["scheduled_date"] = key

        # while e_date >= today and len(t_list) > 0:
        #     for i in range(needed_daily):
        #         if len(t_list) > 0:
        #             callendar[e_date].append(t_list[0])

            # if needed_daily % 2 == 0 or needed_daily == 1:
            #     for i in range(needed_daily):
            #         if len(t_list) > 0:
            #             callendar[e_date].append(t_list[0])
            #             del t_list[0]
            # else:
            #     callendar[e_date].append(t_list[0])
            #     del t_list[0]
            #     for i in range(needed_daily - 1):
            #         if len(t_list) > 0:
            #             callendar[e_date].append(t_list[0])
            #             del t_list[0]
            # e_date -= timedelta(days=1)
