import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import uuid
from core.storage import save

class AddExamWindow:
    def __init__(self, parent, txt, data, btn_style, callback=None):
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.callback = callback

        #   TWORZENIE NOWEGO OKNA
        self.win = tk.Toplevel(parent)
        self.win.resizable(False, False)
        self.win.title(self.txt["win_add_title"])

        # WPROWADZENIE NAZWY PRZEDMIOTU
        tk.Label(self.win, text=self.txt["form_subject"]).grid(row=0, column=0, pady=10, padx=10, sticky="e")
        self.entry_subject = tk.Entry(self.win, width=30)
        self.entry_subject.grid(row=0, column=1, padx=10, pady=10)

        # WPROWADZENIE TYPU EGZAMINU
        tk.Label(self.win, text=self.txt["form_type"]).grid(row=1, column=0, pady=10, padx=10, sticky="e")
        self.entry_title = tk.Entry(self.win, width=30)
        self.entry_title.grid(row=1, column=1, padx=10, pady=10)

        # WPROWADZENIE DATY EGZAMINU
        tk.Label(self.win, text=self.txt["form_date"]).grid(row=2, column=0, pady=10, padx=10, sticky="e")
        self.entry_date = DateEntry(self.win, width=27, date_pattern='y-mm-dd')
        self.entry_date.grid(row=2, column=1, padx=10, pady=10)
        tomorrow = datetime.now() + timedelta(days=1)
        self.entry_date.set_date(tomorrow)

        # WPROWADZENIE LISTY TEMATOW
        tk.Label(self.win, text=self.txt["form_topics_add"]).grid(row=3, column=0, columnspan=2, pady=5)
        self.text_topics = tk.Text(self.win, width=40, height=10)
        self.text_topics.grid(row=4, column=0, columnspan=2, padx=10)

        # PRZYCISKI
        btn_frame = tk.Frame(self.win)
        btn_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=20)

        btn_save = tk.Button(btn_frame, text=self.txt["btn_save"], command=self.save_new_exam, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_exit = tk.Button(btn_frame, text=self.txt["btn_cancel"], command=self.win.destroy, **self.btn_style, activeforeground="red")
        btn_exit.pack(side="left", padx=5)

    # FUNKCJA ZAPISUJACA NOWY EGZAMIN W BAZIE DANYCH
    def save_new_exam(self):
        # zebranie danych egzamin z pól entry
        subject = self.entry_subject.get()
        date_str = self.entry_date.get()
        title = self.entry_title.get()
        topics = self.text_topics.get("1.0", tk.END)

        # zabezpieczenie: jesli pole z data lub tytulem puste to nie pozwol zapisac
        if not subject or not date_str or not title:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_fill_fields"])
            return

        # zamiana tekstu z entry tematow na tablice
        topics_list = [t.strip() for t in topics.split("\n") if t.strip()]
        # nadanie id egzaminu
        exam_id = f"exam_{uuid.uuid4().hex[:8]}"

        # dodanie wpisu z egzaminem do bazy
        new_exam = {
            "id": exam_id,
            "subject": subject,
            "title": title,
            "date": date_str,
        }
        self.data["exams"].append(new_exam)

        # dodanie wpisow z tematami do bazy danych
        for topic in topics_list:
            self.data["topics"].append({
                "id": f"topic_{uuid.uuid4().hex[:8]}", #nadanie kazdemu tematowi wlasnego id
                "exam_id": exam_id,
                "name": topic,
                "status": "todo",
                "scheduled_date": None,
                "locked": False
            })

        save(self.data)

        # callback aby po zapisaniu nowego egzaminu odswiezyc widok planu
        if self.callback:
            self.callback()

        self.win.destroy()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_added"].format(count=len(topics_list)))