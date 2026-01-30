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
        # Sprawdzamy czy egzamin ma być ignorowany jako bariera
        if exam.get("ignore_barrier", False):
            continue  # Nie wstawiamy "E", algorytm nie zobaczy tu ściany

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
            # Filtracja dla trybu "Doplanuj"
            if only_unscheduled:
                if not topic.get("scheduled_date"):
                    topics_list.append(topic["id"])
            else:
                topics_list.append(topic["id"])

    return topics_list


#   GLOWNA FUNKCJA PLANUJACA
def plan(data, only_unscheduled=False):
    today = date.today()
    blocked_set = set(data.get("blocked_dates", []))

    # Tworzymy strukturę kalendarza
    callendar = callendar_create(data, today)

    # Iterujemy po egzaminach
    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date <= today:
            continue

        end_study_date = exam_date - timedelta(days=1)
        if end_study_date < today:
            continue

        # 1. Określamy START okna nauki (skanujemy wstecz do bariery "E")
        scan_date = end_study_date
        while scan_date > today and "E" not in callendar.get(scan_date, []):
            scan_date -= timedelta(days=1)

        start_study_date = scan_date

        # Pobieramy tematy
        t_list = topics_list_create(data, exam["id"], only_unscheduled)

        if not t_list:
            continue

        # 2. Zbieramy listę PRAWIDŁOWYCH dni (niezablokowanych)
        valid_days = []
        curr = start_study_date
        if curr < today: curr = today

        while curr <= end_study_date:
            date_str = str(curr)
            has_exam = "E" in callendar.get(curr, [])

            # Dzień jest valid, jeśli:
            # a) Nie jest zablokowany
            # b) ORAZ (nie ma egzaminu LUB ma egzamin, ale jest to dzień startowy - bariera)
            if date_str not in blocked_set:
                if not has_exam or (has_exam and curr == start_study_date):
                    valid_days.append(curr)

            curr += timedelta(days=1)

        # Sortujemy rosnąco (chronologicznie) - to ważne dla logiki dynamicznej
        valid_days.sort()

        if not valid_days:
            continue

        # 3. ALGORYTM ROZKŁADANIA (DYNAMICZNY + OFFSET)

        days_total = len(valid_days)
        tasks_total = len(t_list)
        start_index = 0

        # LOGIKA OFFSETU (Back-loading):
        # Jeśli mamy mniej zadań niż dni, przesuwamy start, aby zadania były
        # "przyklejone" do egzaminu, a nie do dnia dzisiejszego.
        if tasks_total <= days_total:
            start_index = days_total - tasks_total

        # 4. PĘTLA PLANUJĄCA (Dynamiczna)
        for i in range(start_index, days_total):
            if not t_list:
                break

            current_day = valid_days[i]

            # --- KLUCZOWA ZMIANA: Przeliczamy ile wstawić w TEJ chwili ---
            # Ile dni nam zostało (wliczając ten)?
            days_remaining_in_loop = days_total - i
            # Ile zadań nam zostało?
            tasks_remaining_now = len(t_list)

            # Obliczamy zagęszczenie na bieżąco
            # np. 4 zadania, 3 dni -> ceil(1.33) = 2
            # potem: 2 zadania, 2 dni -> ceil(1.0) = 1
            # potem: 1 zadanie, 1 dzień -> ceil(1.0) = 1
            if days_remaining_in_loop > 0:
                per_day = math.ceil(tasks_remaining_now / days_remaining_in_loop)
            else:
                per_day = tasks_remaining_now

            for _ in range(per_day):
                if t_list:
                    # Bierzemy PIERWSZY temat z listy (zachowanie kolejności w tematach)
                    task_id = t_list.pop(0)

                    if current_day in callendar:
                        callendar[current_day].append(task_id)

    # 5. Zapisanie wyników do bazy danych
    if not only_unscheduled:
        for topic in data["topics"]:
            if topic["status"] == "todo" and not topic.get("locked", False):
                topic["scheduled_date"] = None

    for date_key, items in callendar.items():
        for item_id in items:
            if item_id == "E": continue

            for topic in data["topics"]:
                if topic["id"] == item_id:
                    topic["scheduled_date"] = date_key