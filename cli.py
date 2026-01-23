import uuid
from core.storage import load, save
from core.planner import plan
from datetime import date, timedelta

# terminalowa podstawowa wersja aplikacji zawierająca podstawowe funkcje
# dodawanie egzaminu
# planowanie kalendarza
# oznaczanie tematu jako wykonany
# wyswietlanie planu na najblizszy tydzień


# funkcja nadająca id za pomocą uuid
def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# funkcja dodawania egzaminu razem z tematami
def cmd_add(data):
    subject = input("Przedmiot: ")
    title = input("Forma: ")
    date = input("Data (YYYY-MM-DD): ")

    print("Tematy (pusta linia konczy):")
    topics = []
    while True:
        t = input("> ")
        if not t:
            break
        topics.append(t)

    exam_id = new_id("exam")
    data["exams"].append({
        "id": exam_id,
        "subject": subject,
        "title": title,
        "date": date
    })
    for name in topics:
        data["topics"].append({
            "id": new_id("topic"),
            "exam_id": exam_id,
            "name": name,
            "status": "todo",
            "scheduled_date": None
        })

# funkcja wyswietlajaca plan na najblizszy tydzien
def cmd_week(data):
    today = date.today()
    print("\nPLAN NA NAJBLIŻSZY TYDZIEN:")

    for i in range(7):
        day = today + timedelta(days=i)
        day_str = day.isoformat()
        print(f"\n{day}")
        found = False
        for exam in data["exams"]:
            if exam["date"] == day_str:
                print(f" * {exam["title"].upper()} | {exam["subject"]}")
        for topic in data["topics"]:
            if topic["status"] == "todo" and topic["scheduled_date"] == day_str:
                for exam in data["exams"]:
                    if exam["id"] == topic["exam_id"]:
                        print(f" -{topic["id"]} {exam["subject"]} - {topic["name"]}")
                        found = True
                        break
        if not found:
            print("   brak")

#funkcja oznaczajaca temat jako wykonany
def cmd_done(data, t_id):
    for topic in data["topics"]:
        if topic["id"] == t_id:
            topic["status"] = "done"

# glowna funkcja z petla programu
def main():
    while True:
        data = load()

        print("PLANER NAUKI - CLI")
        print("1 - Dodaj egzamin")
        print("2 - Zaplanuj")
        print("3 - Pokaz tydzien")
        print("4 - Oznacz jako zrobione")
        print("X - Wyjscie")
        choice = input("> ")

        if choice == "1":
            cmd_add(data)
        elif choice == "2":
            plan(data)
            print("planowanie zakonczone")
        elif choice == "3":
            cmd_week(data)
        elif choice == "4":
            t_id = input("ID: ")
            cmd_done(data, t_id)
        elif choice == "X":
            break
        else:
            print("Niepoprawna opcja")

        save(data)

if __name__ == '__main__':
    main()
