import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import uuid
from core.storage import save
from gui.windows.color_picker import ColorPickerWindow

class AddExamWindow:
    def __init__(self, parent, txt, data, btn_style, callback=None):
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.callback = callback

        #   TWORZENIE NOWEGO OKNA
        self.win = ctk.CTkToplevel(parent)
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

        # --- NOWOŚĆ: Checkbox Ignoruj w planowaniu (Bariera) ---
        self.var_ignore_barrier = tk.BooleanVar(value=False)
        cb_text = self.txt.get("form_ignore_barrier", "Ignoruj w planowaniu (Bariera)")
        self.cb_barrier = tk.Checkbutton(self.win, text=cb_text, variable=self.var_ignore_barrier,
                                         onvalue=True, offvalue=False)
        self.cb_barrier.grid(row=3, column=0, columnspan=2, pady=(10, 5))

        # --- NOWOŚĆ: WYBÓR KOLORU (PRZENIESIONE) ---
        # Sprawdzamy aktualny motyw aplikacji
        # Zapisujemy None - czyli "brak wyboru" (domyślny systemowy)
        self.selected_color = None

        # Ale przycisk wizualnie musi mieć kolor pasujący do tła, żeby użytkownik go widział
        mode = ctk.get_appearance_mode()
        btn_visual_color = "#000000" if mode == "Light" else "#ffffff"

        color_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        color_frame.grid(row=4, column=0, columnspan=2, pady=(5, 15))

        tk.Label(color_frame, text=self.txt.get("lbl_color", "Color:")).pack(side="left", padx=5)

        self.btn_color = ctk.CTkButton(color_frame, text="", width=30, height=30,
                                       fg_color=btn_visual_color,  # Wizualnie: kolor tekstu
                                       command=self.open_color_picker)
        self.btn_color.pack(side="left", padx=5)
        # ----------------------------

        # WPROWADZENIE LISTY TEMATOW
        tk.Label(self.win, text=self.txt["form_topics_add"]).grid(row=5, column=0, columnspan=2, pady=(0, 5))
        self.text_topics = tk.Text(self.win, width=40, height=10)
        self.text_topics.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 10))

        # PRZYCISKI
        btn_frame = tk.Frame(self.win)
        btn_frame.grid(row=7, column=0, columnspan=2, padx=20, pady=20)

        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save"], command=self.save_new_exam, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_exit = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.win.destroy, **self.btn_style)
        btn_exit.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        btn_exit.pack(side="left", padx=5)

    def open_color_picker(self):
        def on_color_picked(color):
            self.selected_color = color
            self.btn_color.configure(fg_color=color)

        ColorPickerWindow(self.win, self.txt, self.selected_color, on_color_picked)

    # FUNKCJA ZAPISUJACA NOWY EGZAMIN W BAZIE DANYCH
    def save_new_exam(self):
        # ... (pobieranie danych z pól) ...
        subject = self.entry_subject.get()
        date_str = self.entry_date.get()
        title = self.entry_title.get()
        topics = self.text_topics.get("1.0", tk.END)

        if not subject or not date_str or not title:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_fill_fields"])
            return

        topics_list = [t.strip() for t in topics.split("\n") if t.strip()]
        exam_id = f"exam_{uuid.uuid4().hex[:8]}"

        new_exam = {
            "id": exam_id,
            "subject": subject,
            "title": title,
            "date": date_str,
            "ignore_barrier": self.var_ignore_barrier.get(),
            "color": self.selected_color  # <--- DODANO TO POLE
        }
        self.data["exams"].append(new_exam)

        # --- AKTUALIZACJA GLOBALNYCH STATYSTYK (Egzaminy) ---
        if "global_stats" not in self.data: self.data["global_stats"] = {}
        curr_exams = self.data["global_stats"].get("exams_added", 0)
        self.data["global_stats"]["exams_added"] = curr_exams + 1
        # ----------------------------------------------------

        for topic in topics_list:
            self.data["topics"].append({
                "id": f"topic_{uuid.uuid4().hex[:8]}",
                "exam_id": exam_id,
                "name": topic,
                "status": "todo",
                "scheduled_date": None,
                "locked": False
            })

        save(self.data)

        self.win.destroy()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_added"].format(count=len(topics_list)))

        if self.callback:
            self.callback()