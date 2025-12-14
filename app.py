import uuid
import argparse
from storage import load, save
from planner import plan
from datetime import date, timedelta

def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

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

def cmd_done(data, t_id):
    for topic in data["topics"]:
        if topic["id"] == t_id:
            topic["status"] = "done"

def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument("cmd", choices=["add","plan","week"])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("add")
    sub.add_parser("plan")
    sub.add_parser("week")

    p_done = sub.add_parser("done")
    p_done.add_argument("topic_id")

    args = parser.parse_args()

    data = load()

    if args.cmd == "add":
        cmd_add(data)

    if args.cmd == "plan":
        plan(data)
        print("planowanie zakonczone")

    if args.cmd == "week":
        cmd_week(data)

    if args.cmd == "done":
        cmd_done(data, args.topic_id)

    save(data)

if __name__ == '__main__':
    main()
