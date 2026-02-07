from datetime import datetime, date, timedelta
import math


#   FUNKCJA ZMIENIAJACA NA FORMAT DATY
def date_format(text):
    if isinstance(text, date):
        return text
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        # Fallback na dzisiaj w przypadku błędu danych
        return date.today()


#   FUNKCJA TWORZACA PUSTA TABLICE KALENDARZA
def callendar_create(storage, tday):
    callendar = {}
    # Pobieramy egzaminy on-demand bezpośrednio z SQL
    exams = storage.get_exams()

    # Tworzymy zakres dat od dziś do najdalszego egzaminu
    max_date = tday
    for exam in exams:
        if not exam["date"]:
            continue
        exam_date = date_format(exam["date"])
        if exam_date > max_date:
            max_date = exam_date

    # Wypełniamy kalendarz pustymi listami
    curr = max_date
    while curr >= tday:
        callendar[curr] = []
        curr -= timedelta(days=1)

    # Wstawiamy znaczniki egzaminów "E"
    for exam in exams:
        # Sprawdzamy czy egzamin ma być ignorowany jako bariera
        # sqlite3.Row zwraca int (0/1), Python traktuje 0 jako False
        if exam["ignore_barrier"]:
            continue  # Nie wstawiamy "E", algorytm nie zobaczy tu ściany

        if not exam["date"]:
            continue

        exam_date = date_format(exam["date"])
        if exam_date >= tday:
            callendar[exam_date] = ["E"]

    return callendar


#   FUNKCJA TWORZACA LISTE TEMATOW DO WSTAWIENIA W KALENDARZ
def topics_list_create(storage, e_id, only_unscheduled=False):
    topics_list = []
    today = date.today()

    # Pobieramy dane on-demand
    exams = storage.get_exams()
    # Optymalizacja: pobieramy tematy tylko dla danego egzaminu (SQL Filtering)
    exam_topics = storage.get_topics(exam_id=e_id)

    # Znajdź datę egzaminu
    exam_date = None
    for exam in exams:
        if exam["id"] == e_id:
            if exam["date"]:
                exam_date = date_format(exam["date"])
            break

    if exam_date is None or exam_date <= today:
        return topics_list

    # Zbierz tematy
    for topic in exam_topics:
        # topic['locked'] to int 0/1, co działa poprawnie z 'not' (not 0 -> True)
        is_valid = (topic["status"] == "todo" and not topic["locked"])

        if is_valid:
            # Filtracja dla trybu "Doplanuj"
            if only_unscheduled:
                if not topic["scheduled_date"]:
                    topics_list.append(topic["id"])
            else:
                topics_list.append(topic["id"])

    return topics_list


#   GLOWNA FUNKCJA PLANUJACA
def plan(storage, only_unscheduled=False):
    today = date.today()

    # 1. Pobieramy dane wejściowe on-demand (Pure SQL)
    # blocked_dates to lista stringów, rzutujemy na set dla O(1) lookup
    blocked_set = set(storage.get_blocked_dates())
    exams = storage.get_exams()

    # 2. Tworzymy strukturę kalendarza
    callendar = callendar_create(storage, today)

    # 3. Iterujemy po egzaminach (Algorytm)
    for exam in exams:
        if not exam["date"]:
            continue

        exam_date = date_format(exam["date"])
        if exam_date <= today:
            continue

        end_study_date = exam_date - timedelta(days=1)
        if end_study_date < today:
            continue

        # Określamy START okna nauki (skanujemy wstecz do bariery "E")
        scan_date = end_study_date
        while scan_date > today and "E" not in callendar.get(scan_date, []):
            scan_date -= timedelta(days=1)

        start_study_date = scan_date

        # Pobieramy listę ID tematów do zaplanowania dla tego egzaminu
        t_list = topics_list_create(storage, exam["id"], only_unscheduled)

        if not t_list:
            continue

        # Zbieramy listę PRAWIDŁOWYCH dni (niezablokowanych)
        valid_days = []
        curr = start_study_date
        if curr < today: curr = today

        while curr <= end_study_date:
            has_exam = "E" in callendar.get(curr, [])

            # Konwersja date -> string dla porównania z bazą blocked_dates (TEXT)
            curr_str = str(curr)

            # Dzień jest valid, jeśli:
            # a) Nie jest zablokowany
            # b) ORAZ (nie ma egzaminu LUB ma egzamin, ale jest to dzień startowy - bariera)
            if curr_str not in blocked_set:
                if not has_exam or (has_exam and curr == start_study_date):
                    valid_days.append(curr)

            curr += timedelta(days=1)

        # Sortujemy rosnąco (chronologicznie)
        valid_days.sort()

        if not valid_days:
            continue

        # ALGORYTM ROZKŁADANIA (DYNAMICZNY + OFFSET)
        days_total = len(valid_days)
        tasks_total = len(t_list)
        start_index = 0

        # LOGIKA OFFSETU (Back-loading):
        # Jeśli mamy mniej zadań niż dni, przesuwamy start, aby zadania były
        # "przyklejone" do egzaminu, a nie do dnia dzisiejszego.
        if tasks_total <= days_total:
            start_index = days_total - tasks_total

        # PĘTLA PLANUJĄCA
        for i in range(start_index, days_total):
            if not t_list:
                break

            current_day = valid_days[i]

            # Przeliczamy zagęszczenie dynamicznie
            days_remaining_in_loop = days_total - i
            tasks_remaining_now = len(t_list)

            if days_remaining_in_loop > 0:
                per_day = math.ceil(tasks_remaining_now / days_remaining_in_loop)
            else:
                per_day = tasks_remaining_now

            for _ in range(per_day):
                if t_list:
                    # Bierzemy PIERWSZY temat z listy (zachowanie kolejności)
                    task_id = t_list.pop(0)

                    if current_day in callendar:
                        callendar[current_day].append(task_id)

    # 4. Zapisanie wyników do bazy danych

    # Pobieramy wszystkie tematy i konwertujemy na dict (mutable),
    # aby móc je zmodyfikować i zapisać z powrotem.
    # Używamy get_topics() bez filtrów, by mieć pełną mapę do aktualizacji.
    all_topics = [dict(t) for t in storage.get_topics()]
    topics_map = {t["id"]: t for t in all_topics}

    # Krok A: Resetowanie dat (chyba że tryb only_unscheduled)
    if not only_unscheduled:
        for topic in all_topics:
            if topic["status"] == "todo" and not topic["locked"]:
                topic["scheduled_date"] = None

    # Krok B: Przypisanie nowych dat z kalendarza
    for date_key, items in callendar.items():
        for item_id in items:
            if item_id == "E": continue

            if item_id in topics_map:
                # Konwersja daty na string dla bazy SQL (TEXT)
                topics_map[item_id]["scheduled_date"] = str(date_key)

    # Krok C: Commit zmian do StorageManager
    # Aktualizujemy wszystkie tematy, aby odzwierciedlić zarówno nowe daty, jak i resety (None)
    for topic in all_topics:
        storage.update_topic(topic)