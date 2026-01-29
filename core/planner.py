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

    # Tworzymy zakres dat od dziś do najdalszego egzaminu
    max_date = tday
    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date > max_date:
            max_date = exam_date

    # Wypełniamy kalendarz pustymi listami
    curr = max_date
    while curr >= tday:
        callendar[curr] = []
        curr -= timedelta(days=1)

    # Wstawiamy znaczniki egzaminów "E"
    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date >= tday:
            callendar[exam_date] = ["E"]

    return callendar


#   FUNKCJA TWORZACA LISTE TEMATOW DO WSTAWIENIA W KALENDARZ
def topics_list_create(data, e_id, only_unscheduled=False):
    topics_list = []
    today = date.today()

    # Znajdź datę egzaminu
    exam_date = None
    for exam in data["exams"]:
        if exam["id"] == e_id:
            exam_date = date_format(exam["date"])
            break

    if exam_date is None or exam_date <= today:
        return topics_list

    # Zbierz tematy
    for topic in data["topics"]:
        # Sprawdzamy standardowe warunki
        is_valid = (topic["exam_id"] == e_id and
                    topic["status"] == "todo" and
                    not topic.get("locked", False))

        if is_valid:
            # --- NOWOŚĆ: Filtracja dla trybu "Doplanuj" ---
            if only_unscheduled:
                # Jeśli tryb "tylko nowe", bierzemy tylko te, które NIE mają daty
                if not topic.get("scheduled_date"):
                    topics_list.append(topic["id"])
            else:
                # Tryb pełny - bierzemy wszystko
                topics_list.append(topic["id"])

    return topics_list


#   GLOWNA FUNKCJA PLANUJACA
def plan(data, only_unscheduled=False):
    today = date.today()
    blocked_set = set(data.get("blocked_dates", []))

    # Tworzymy strukturę kalendarza (pustą - zawiera tylko znaczniki E)
    # W trybie "Doplanuj" kalendarz technicznie nie widzi starych zadań w tej zmiennej 'callendar',
    # ale to dobrze - nowe zadania po prostu "dokleją się" do dni.
    callendar = callendar_create(data, today)

    # Iterujemy po egzaminach
    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date <= today:
            continue

        end_study_date = exam_date - timedelta(days=1)
        if end_study_date < today:
            continue

        # 1. Określamy START okna nauki
        scan_date = end_study_date
        while scan_date > today and "E" not in callendar.get(scan_date, []):
            scan_date -= timedelta(days=1)

        start_study_date = scan_date
        if "E" in callendar.get(start_study_date, []):
            start_study_date += timedelta(days=1)

        # --- ZMIANA: Pobieramy listę z uwzględnieniem trybu ---
        t_list = topics_list_create(data, exam["id"], only_unscheduled)

        if not t_list:
            continue

        # 2. Zbieramy listę PRAWIDŁOWYCH dni (niezablokowanych)
        valid_days = []
        curr = start_study_date
        if curr < today: curr = today

        while curr <= end_study_date:
            date_str = str(curr)
            if date_str not in blocked_set and "E" not in callendar.get(curr, []):
                valid_days.append(curr)
            curr += timedelta(days=1)

        if not valid_days:
            continue

        # 3. ODWRACAMY listę dni (Logika Back-loadingu)
        valid_days.sort(reverse=True)

        # 4. Algorytm Rozkładania
        for i, day in enumerate(valid_days):
            if not t_list:
                break

            slots_left = len(valid_days) - i
            tasks_left = len(t_list)

            per_day = math.ceil(tasks_left / slots_left)

            for _ in range(per_day):
                if t_list:
                    task_id = t_list.pop()
                    if day in callendar:
                        callendar[day].append(task_id)

    # 5. Zapisanie wyników do bazy danych

    # --- ZMIANA: Czyścimy stare daty TYLKO w trybie pełnym ---
    if not only_unscheduled:
        for topic in data["topics"]:
            if topic["status"] == "todo" and not topic.get("locked", False):
                topic["scheduled_date"] = None

    # Przypisujemy nowe daty z kalendarza
    # W trybie 'only_unscheduled' kalendarz zawiera tylko nowe zadania, więc tylko one dostaną daty.
    for date_key, items in callendar.items():
        for item_id in items:
            if item_id == "E": continue

            for topic in data["topics"]:
                if topic["id"] == item_id:
                    topic["scheduled_date"] = date_key