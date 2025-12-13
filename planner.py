from datetime import datetime, date, timedelta
import math

def parse_date(text):
    return datetime.strptime(text, "%Y-%m-%d").date()

def plan(data):
    pref_max_per_day = data["settings"].get("max_per_day", 2)
    pref_max_same_subject = data["settings"].get("max_same_subject_per_day", 1)
    today = date.today()

    exams_by_id = {e["id"]: e for e in data["exams"]}

    tasks = []
    for topic in data["topics"]:
        if topic["status"] == "todo" and topic["scheduled_date"] is None:
            exam = exams_by_id[topic["exam_id"]]
            deadline = parse_date(exam["date"])
            subject = exam["subject"]
            tasks.append({"deadline": deadline, "subject": subject, "topic": topic})

    tasks.sort(key=lambda t: t["deadline"])

    if not tasks:
        return

    last_day = max(t["deadline"] for t in tasks) - timedelta(days=1)
    day = today

    while day <= last_day and tasks:
        tasks = [t for t in tasks if t["deadline"] > day]

        if not tasks:
            break

        remaining_days = (last_day - day).days + 1
        remaining_tasks = len(tasks)

        required_per_day = math.ceil(remaining_tasks / remaining_days)

        day_limit = max(pref_max_per_day, required_per_day)

        used_subject_count = {}
        picked = []

        for i, t in enumerate(tasks):
            if len(picked) >= day_limit:
                break
            subj = t["subject"]
            if pref_max_same_subject > 0 and used_subject_count.get(subj, 0) >= pref_max_same_subject:
                continue
            picked.append(i)
            used_subject_count[subj] = used_subject_count.get(subj, 0) + 1

        if len(picked) < day_limit:
            for i, t in enumerate(tasks):
                if len(picked) >= day_limit:
                    break
                if i in picked:
                    continue
                picked.append(i)

        for i in picked:
            tasks[i]["topic"]["scheduled_date"] = day.isoformat()

        for i in sorted(picked, reverse=True):
            tasks.pop(i)

        day += timedelta(days=1)