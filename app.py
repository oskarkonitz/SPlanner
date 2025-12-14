import uuid
import argparse
from storage import load, save
from planner import plan

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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["add","plan"])
    args = parser.parse_args()

    data = load()

    if args.cmd == "add":
        cmd_add(data)

    if args.cmd == "plan":
        plan(data)
        print("planowanie zakonczone")

    save(data)

if __name__ == '__main__':
    main()
