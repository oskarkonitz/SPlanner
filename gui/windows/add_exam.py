import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import uuid
import random


class AddExamWindow:
    def __init__(self, parent, txt, btn_style, callback=None, storage=None):
        self.txt = txt
        self.btn_style = btn_style
        self.callback = callback
        self.storage = storage  # Przechowujemy instancję StorageManagera

        # Pobieramy listę przedmiotów z bazy do listy rozwijanej
        self.db_subjects = []
        self.subject_names = []
        self.semesters = []

        if self.storage:
            self.db_subjects = [dict(s) for s in self.storage.get_subjects()]
            self.subject_names = [s["name"] for s in self.db_subjects]
            self.semesters = [dict(s) for s in self.storage.get_semesters()]

        #   TWORZENIE NOWEGO OKNA
        self.win = ctk.CTkToplevel(parent)
        self.win.resizable(False, False)
        self.win.title(self.txt["win_add_title"])

        # WPROWADZENIE NAZWY PRZEDMIOTU (Zmieniono na ComboBox + Przycisk Filtra)
        tk.Label(self.win, text=self.txt["form_subject"]).grid(row=0, column=0, pady=10, padx=10, sticky="e")

        # Kontener na combobox i przycisk, aby były obok siebie
        subj_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        subj_frame.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.combo_subject = ctk.CTkComboBox(subj_frame, width=200, values=self.subject_names,
                                             command=self.on_subject_change)
        self.combo_subject.pack(side="left")

        # Puste pole na start
        self.combo_subject.set("")

        # Przycisk filtrowania semestru
        self.btn_sem_filter = ctk.CTkButton(subj_frame, text="📅", width=30, height=28,
                                            fg_color="transparent", border_width=1, border_color="gray",
                                            text_color=("gray10", "gray90"),
                                            command=self.open_semester_menu)
        self.btn_sem_filter.pack(side="left", padx=(5, 0))

        # WPROWADZENIE TYPU EGZAMINU
        tk.Label(self.win, text=self.txt["form_type"]).grid(row=1, column=0, pady=10, padx=10, sticky="e")
        self.entry_title = tk.Entry(self.win, width=30)
        self.entry_title.grid(row=1, column=1, padx=10, pady=10)

        # WPROWADZENIE DATY
        tk.Label(self.win, text=self.txt["form_date"]).grid(row=2, column=0, pady=10, padx=10, sticky="e")
        self.entry_date = DateEntry(self.win, width=27, date_pattern='y-mm-dd')
        self.entry_date.grid(row=2, column=1, padx=10, pady=10)

        # WPROWADZENIE GODZINY (NOWOŚĆ)
        tk.Label(self.win, text=self.txt.get("form_time", "Time (HH:MM)")).grid(row=3, column=0, pady=10, padx=10, sticky="e")
        self.entry_time = tk.Entry(self.win, width=30)
        self.entry_time.insert(0, "09:00") # Domyślna godzina
        self.entry_time.grid(row=3, column=1, padx=10, pady=10)

        # CHECKBOX BARIERY
        self.var_ignore_barrier = tk.BooleanVar(value=False)
        cb_text = self.txt.get("form_ignore_barrier", "Ignoruj w planowaniu (Bariera)")
        self.cb_barrier = tk.Checkbutton(self.win, text=cb_text, variable=self.var_ignore_barrier,
                                         onvalue=True, offvalue=False)
        self.cb_barrier.grid(row=4, column=0, columnspan=2, pady=(10, 5))

        # USUNIĘTO SEKCJĘ KOLORU (Color Preview) ZGODNIE Z PROŚBĄ
        self.selected_color = None

        # WPROWADZENIE TEMATÓW
        tk.Label(self.win, text=self.txt["form_topics_add"]).grid(row=6, column=0, pady=(0, 5), columnspan=2)
        self.text_topics = tk.Text(self.win, width=40, height=10)
        self.text_topics.grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 10))

        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)

        # PRZYCISK ZAPISU
        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save"], command=self.save_exam, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_cancel = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.win.destroy, **self.btn_style)
        btn_cancel.pack(side="left", padx=5)
        btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

    def open_semester_menu(self):
        """Wyświetla menu wyboru semestru obok przycisku."""
        menu = tk.Menu(self.win, tearoff=0)

        # Opcja "Wszystkie"
        menu.add_command(label=self.txt.get("val_all", "All"),
                         command=lambda: self.filter_subjects_by_semester(None))
        menu.add_separator()

        # Sortowanie semestrów (Aktualny pierwszy)
        sorted_semesters = sorted(self.semesters, key=lambda x: (not x["is_current"], x["start_date"]), reverse=True)

        for sem in sorted_semesters:
            label_text = sem["name"]
            if sem["is_current"]:
                label_text += f" ({self.txt.get('tag_current', 'Current')})"

            menu.add_command(label=label_text,
                             command=lambda s_id=sem["id"]: self.filter_subjects_by_semester(s_id))

        # Wyświetlenie menu w miejscu przycisku
        try:
            x = self.btn_sem_filter.winfo_rootx()
            y = self.btn_sem_filter.winfo_rooty() + self.btn_sem_filter.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def filter_subjects_by_semester(self, semester_id):
        """Aktualizuje listę przedmiotów w ComboBox na podstawie wybranego semestru."""
        if semester_id is None:
            # Pokaż wszystkie
            filtered_names = [s["name"] for s in self.db_subjects]
        else:
            # Filtruj po ID
            filtered_names = [s["name"] for s in self.db_subjects if s["semester_id"] == semester_id]

        if not filtered_names:
            filtered_names = [""]

        self.combo_subject.configure(values=filtered_names)
        self.combo_subject.set("")  # Reset wyboru po zmianie filtra

    def on_subject_change(self, choice):
        """Aktualizuje kolor w zmiennej na podstawie wybranego przedmiotu (bez wizualizacji)."""
        found = False
        for sub in self.db_subjects:
            if sub["name"] == choice:
                self.selected_color = sub["color"]
                found = True
                break

        if not found:
            # Jeśli wpisano nową nazwę, kolor pozostaje None (zostanie wylosowany przy zapisie)
            self.selected_color = None

    def save_exam(self):
        subject_name = self.combo_subject.get().strip()
        title = self.entry_title.get().strip()
        date_val = self.entry_date.get()
        time_val = self.entry_time.get().strip() # Pobranie godziny
        topics_raw = self.text_topics.get("1.0", tk.END).strip()

        if not subject_name or not title or not date_val:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_fill_fields"])
            return

        if not self.storage:
            print("[AddExamWindow] CRITICAL: StorageManager not provided!")
            return

        # --- LOGIKA PRZEDMIOTU (Subject) ---
        subject_id = None
        subject_color = self.selected_color

        # 1. Sprawdź czy przedmiot już istnieje
        for sub in self.db_subjects:
            if sub["name"] == subject_name:
                subject_id = sub["id"]
                # Używamy koloru z bazy, chyba że self.selected_color został już ustawiony
                if not subject_color:
                    subject_color = sub["color"]
                break

        # 2. Jeśli nie istnieje -> Utwórz nowy przedmiot
        if not subject_id:
            # Losujemy kolor dla nowego przedmiotu, bo to nowy wpis
            random_colors = ["#e74c3c", "#8e44ad", "#3498db", "#1abc9c", "#f1c40f", "#e67e22", "#2ecc71"]
            subject_color = random.choice(random_colors)

            # Pobieramy ID semestru (bierzemy pierwszy dostępny lub tworzymy domyślny)
            semesters = self.storage.get_semesters()
            semester_id = None
            if semesters:
                # Preferuj aktualny
                curr = [s for s in semesters if s["is_current"]]
                if curr:
                    semester_id = curr[0]["id"]
                else:
                    semester_id = semesters[0]["id"]
            else:
                # Tworzenie semestru awaryjnie
                semester_id = f"sem_{uuid.uuid4().hex[:8]}"
                self.storage.add_semester({
                    "id": semester_id,
                    "name": "Default Semester",
                    "start_date": str(datetime.now().date()),
                    "end_date": str((datetime.now() + timedelta(days=180)).date()),
                    "is_current": 1
                })

            subject_id = f"sub_{uuid.uuid4().hex[:8]}"
            short_name = subject_name[:3].upper()

            self.storage.add_subject({
                "id": subject_id,
                "semester_id": semester_id,
                "name": subject_name,
                "short_name": short_name,
                "color": subject_color,
                "weight": 1.0
            })

        # --- TWORZENIE EGZAMINU ---
        exam_id = f"exam_{uuid.uuid4().hex[:8]}"

        # Przygotowanie obiektu egzaminu
        new_exam = {
            "id": exam_id,
            "subject_id": subject_id,  # Klucz relacji
            "subject": subject_name,  # Legacy
            "title": title,
            "date": date_val,
            "time": time_val, # Dodana godzina
            "note": "",
            "ignore_barrier": self.var_ignore_barrier.get(),
            "color": subject_color  # Legacy/Cache
        }

        self.storage.add_exam(new_exam)

        # --- AKTUALIZACJA GLOBALNYCH STATYSTYK ---
        global_stats = self.storage.get_global_stats()
        curr_exams = global_stats.get("exams_added", 0)
        self.storage.update_global_stat("exams_added", curr_exams + 1)

        # --- ZAPIS TEMATÓW ---
        topics_list = [t.strip() for t in topics_raw.split('\n') if t.strip()]
        for topic in topics_list:
            new_topic = {
                "id": f"topic_{uuid.uuid4().hex[:8]}",
                "exam_id": exam_id,
                "name": topic,
                "status": "todo",
                "scheduled_date": None,
                "locked": False,
                "note": ""
            }
            self.storage.add_topic(new_topic)

        self.win.destroy()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_added"].format(count=len(topics_list)))

        if self.callback:
            self.callback()