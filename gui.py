import tkinter as tk
from tkinter import messagebox
from storage import load, save
from planner import plan
import uuid
from datetime import datetime, timedelta

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Planer Nauki v1.0")
        self.root.geometry("400x400")

        self.data = load()
        print(f"Loaded exams: {len(self.data["exams"])}")

        self.label_title = tk.Label(self.root, text="Planer Nauki", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=20)
        self.btn_add = tk.Button(self.root, text="Dodaj Egzamin", width=20, height=2, command=self.add_window)
        self.btn_add.pack(pady=10)
        self.btn_plan = tk.Button(self.root, text="Generuj Plan", width=20, height=2, command=self.run_planner)
        self.btn_plan.pack(pady=10)
        self.btn_week = tk.Button(self.root, text="Pokaż Tydzień", width=20, height=2, command=self.show_week)
        self.btn_week.pack(pady=10)
        self.btn_exit = tk.Button(self.root, text="Wyjście", width=20, height=2, command=self.root.quit)
        self.btn_exit.pack(pady=20)

    def run_planner(self):
        try:
            plan(self.data)
            save(self.data)
            messagebox.showinfo("Sukces", "Planowanie zakonczone")
        except Exception as e:
            messagebox.showerror("Error", e)

    def add_window(self):
        def save_new_exam():
            subject = entry_subject.get()
            date_str = entry_date.get()
            title = entry_title.get()
            topics = text_topics.get("1.0", tk.END)

            if not subject or not date_str or not title:
                messagebox.showwarning("Błąd!", "Uzupelnij brakujace pola")
                return

            topics_list = [t.strip() for t in topics.split("\n") if t.strip()]
            exam_id = f"exam_{uuid.uuid4().hex[:8]}"

            new_exam = {
                "id": exam_id,
                "subject": subject,
                "title": title,
                "date": date_str,
            }
            self.data["exams"].append(new_exam)

            for topic in topics_list:
                self.data["topics"].append({
                    "id": f"topic_{uuid.uuid4().hex[:8]}",
                    "exam_id": exam_id,
                    "name": topic,
                    "status": "todo",
                    "scheduled_date": None
                })

            save(self.data)
            messagebox.showinfo("Sukces", f"Dodano egzamin i {len(topics_list)} tematów")
            add_win.destroy()

        add_win = tk.Toplevel(self.root)
        add_win.geometry("460x400")
        add_win.title("Dodaj nowy egzamin")

        tk.Label(add_win, text="Przedmiot:").grid(row=0, column=0, pady=10, padx=10, sticky="e")
        entry_subject = tk.Entry(add_win, width=30)
        entry_subject.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(add_win, text="Forma:").grid(row=1, column=0, pady=10, padx=10, sticky="e")
        entry_title = tk.Entry(add_win, width=30)
        entry_title.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(add_win, text="Data (YYYY-MM-DD):").grid(row=2, column=0, pady=10, padx=10, sticky="e")
        entry_date = tk.Entry(add_win, width=30)
        entry_date.grid(row=2, column=1, padx=10, pady=10)
        tommorow = datetime.now() + timedelta(days=1)
        entry_date.insert(0, tommorow.strftime("%Y-%m-%d"))

        tk.Label(add_win, text="Tematy (jeden pod drugim):").grid(row=3, column=0, columnspan=2, pady=5)
        text_topics = tk.Text(add_win, width=40, height=10)
        text_topics.grid(row=4, column=0, columnspan=2, padx=10)

        btn_save = tk.Button(add_win, text="ZAPISZ", command=save_new_exam, height=2, width=15)
        btn_save.grid(row=5, column=0, columnspan=2, pady=20)

    def show_week(self):
        messagebox.showinfo("abc", "def")



if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()