from datetime import datetime, date, timedelta
import math


# FUNKCJA POMOCNICZA: Formatowanie daty
def date_format(text):
    if isinstance(text, date):
        return text
    return datetime.strptime(text, "%Y-%m-%d").date()


# NOWA FUNKCJA POMOCNICZA: Liczy ile dni roboczych zostało w przedziale
def count_valid_days(start_date, end_date, blocked_set):
    count = 0
    curr = start_date
    while curr <= end_date:
        # Liczymy dzień tylko jeśli NIE jest zablokowany
        if str(curr) not in blocked_set:
            count += 1
        curr += timedelta(days=1)
    return count


# FUNKCJA TWORZACA PUSTA TABLICE KALENDARZA
def callendar_create(data, tday):
    callendar = {}
    max_date = tday

    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date < tday:
            continue
        if exam_date > max_date:
            max_date = exam_date

    while max_date >= tday:
        callendar.update({max_date: []})
        max_date -= timedelta(days=1)

    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date < tday:
            continue
        callendar.update({exam_date: ["E"]})

    return callendar


# FUNKCJA TWORZACA LISTE TEMATOW DO WSTAWIENIA W KALENDARZ
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
        # Dodano warunek na "locked", reszta bez zmian
        if topic["exam_id"] == e_id and topic["status"] == "todo" and not topic.get("locked", False):
            topics_list.append(topic["id"])

    return topics_list


# GLOWNA FUNKCJA PLANUJACA (Oryginalna z obsługą blocked_dates)
def plan(data):
    today = date.today()
    blocked_set = set(data.get("blocked_dates", []))

    # stworzenie pustego kalendarza
    callendar = callendar_create(data, today)

    # przypisanie dat dla kazdego egzaminu pokolei
    for exam in data["exams"]:
        exam_date = date_format(exam["date"])
        if exam_date <= today:
            continue

        end_study_date = exam_date - timedelta(days=1)  # definicja konca dla egzaminu

        if end_study_date < today:
            continue

        scan_date = end_study_date  # definicja startu dla egzaminu

        # Szukamy najwcześniejszego możliwego dnia startu (ORYGINALNA LOGIKA)
        # Skanujemy wstecz aż trafimy na inny egzamin "E" lub dzisiaj.
        # Nie pomijamy tu blocked_dates, bo okno czasowe jest stałe.
        while scan_date > today and "E" not in callendar.get(scan_date, []):
            scan_date -= timedelta(days=1)

        start_study_date = scan_date

        # zabezpieczenie jesli dzis jest po koncu nauki
        if start_study_date > end_study_date:
            continue

        t_list = topics_list_create(data, exam["id"])  # liczenie tematów
        if not t_list:
            continue

        # --- ORYGINALNA LOGIKA Z MODYFIKACJĄ DLA ZABLOKOWANYCH DNI ---

        # 1. Zamiast (end - start).days + 1, używamy count_valid_days
        # Dzięki temu "dni_window" to tylko te dni, w które faktycznie można się uczyć
        days_window_valid = count_valid_days(start_study_date, end_study_date, blocked_set)

        tasks_count = len(t_list)

        # 2. Obliczamy dni "nadmiarowe" (surplus)
        # Jeśli mamy 5 dni ważnych, a 2 tematy, to 3 dni możemy pominąć na początku
        surplus_days = 0
        if days_window_valid > tasks_count:
            surplus_days = days_window_valid - tasks_count

        # 3. Pętla planująca (Oryginalna - do przodu)
        current_day = start_study_date

        while current_day <= end_study_date:

            # A. ZABEZPIECZENIE: Jeśli dzień jest zablokowany, pomijamy go całkowicie
            if str(current_day) in blocked_set:
                current_day += timedelta(days=1)
                continue

            # B. LOGIKA SURPLUS (Oryginalna)
            # Jeśli mamy nadmiar dni, pomijamy ten dzień (żeby skumulować naukę przed egzaminem)
            if surplus_days > 0:
                surplus_days -= 1
                current_day += timedelta(days=1)
                continue

            # C. WPISYWANIE ZADAŃ
            if current_day in callendar:

                # Dynamicznie liczymy ile dni roboczych zostało od TERAZ do końca
                # Tu też zmiana: używamy count_valid_days zamiast zwykłego odejmowania
                valid_days_left = count_valid_days(current_day, end_study_date, blocked_set)
                topics_left = len(t_list)

                if valid_days_left > 0 and topics_left > 0:
                    # Dzielimy pozostałą pracę przez pozostały czas
                    daily_count = math.ceil(topics_left / valid_days_left)
                else:
                    daily_count = 0

                for i in range(daily_count):
                    if len(t_list) > 0:
                        callendar[current_day].append(t_list[0])
                        del t_list[0]

            current_day += timedelta(days=1)

    # PRZYPISANIE DAT DLA TEMATOW W BAZIE
    for topic in data["topics"]:
        if topic["status"] == "todo" and not topic.get("locked", False):
            topic["scheduled_date"] = None

        for key, value in callendar.items():
            if topic["id"] in value:
                topic["scheduled_date"] = key