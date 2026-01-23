from datetime import datetime, date, timedelta
import math

#   FUNKCJA ZMIENIAJACA NA FORMAT DATY
def date_format(text):
    if isinstance(text, date):
        return text
    return datetime.strptime(text, "%Y-%m-%d").date()


#   FUNKCJA TWORZACA PUSTA TABLICE KALENDARZA
def callendar_create(data, tday):
    callendar = {}
    max_date = tday

    for exam in data["exams"]:
        # if date_format(exam["date"]) > max_date:
        #     max_date = date_format(exam["date"])
        exam_date = date_format(exam["date"])
        if exam_date < tday:
            continue
        if exam_date > max_date:
            max_date = exam_date

    while max_date >= tday:
        callendar.update({max_date : []})
        max_date -= timedelta(days=1)

    for exam in data["exams"]:
        # callendar.update({date_format(exam["date"]): ["E"]})
        exam_date = date_format(exam["date"])
        if exam_date < tday:
            continue
        callendar.update({exam_date : ["E"]})

    return callendar

#   FUNKCJA TWORZACA LISTE TEMATOW DO WSTAWIENIA W KALENDARZ
def topics_list_create(data, e_id):
    topics_list = []
    today = date.today()
    exam_date = None

    for exam in data["exams"]:
        if exam["id"] == e_id:
            exam_date = date_format(exam["date"])
            break

    if exam_date is None or exam_date <= today:
        return topics_list

    for topic in data["topics"]:
        if topic["exam_id"] == e_id and topic["status"] == "todo" and not topic.get("locked", False):
            topics_list.append(topic["id"])

    return topics_list

#   STARA NIEUZYWANA FUNKCJA PLANOWANIA TEMATOW
def plan_old(data):
    pref_max_per_day = data["settings"].get("max_per_day", 2)
    pref_max_same_subject = data["settings"].get("max_same_subject_per_day", 1)
    today = date.today()

    callendar = callendar_create(data, today)

    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date <= today:
            continue

        e_date = exam_date - timedelta(days=1)
        if e_date not in callendar:
            continue

        border_day = e_date
        while border_day > today and "E" not in callendar.get(border_day, []):
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

#   FUNKCJA PLANOWANIA DAT DLA TEMATOW
def plan(data):
    today = date.today()

    #stworzenie pustego kalendarza
    callendar = callendar_create(data, today)

    # przypisanie dat dla kazdego egzaminu pokolei
    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date <= today:
            continue

        end_study_date = exam_date - timedelta(days=1) #    definicja konca dla egzaminu

        if end_study_date < today:
            continue

        scan_date = end_study_date  #   definicja startu dla egzaminu
        while scan_date > today and "E" not in callendar.get(scan_date, []):
            scan_date -= timedelta(days=1)

        start_study_date = scan_date

        # zabezpieczenie jesli dzis jest po koncu nauki
        if start_study_date > end_study_date:
            continue

        t_list = topics_list_create(data, exam["id"])   #   liczenie tematów
        if not t_list:
            continue

        days_available = (end_study_date - start_study_date).days + 1

        # zabezpieczenie przed dzieleniem przez zero
        if days_available <= 0:
            days_available = 1

        needed_daily = math.ceil(len(t_list) / days_available)

        current_day = start_study_date

        if needed_daily == 1:   #   logika planowania jeśli 1 egzamin dziennie
            tasks_count = len(t_list)
            offset = days_available - tasks_count
            if offset < 0:
                offset = 0
            current_day = start_study_date + timedelta(days=offset)

        #        PETLA PLANUJĄCA
        while current_day <= end_study_date:
            if current_day in callendar:
                for i in range(needed_daily):
                    if len(t_list) > 0:
                        callendar[current_day].append(t_list[0])
                        del t_list[0]

            current_day += timedelta(days=1)

    #       PRZYPISANIE DAT DLA TEMATOW W BAZIE
    for topic in data["topics"]:
        if topic["status"] == "todo" and not topic.get("locked", False):
            topic["scheduled_date"] = None

        for key, value in callendar.items():
            if topic["id"] in value:
                topic["scheduled_date"] = key
