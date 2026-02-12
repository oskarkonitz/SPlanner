import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import uuid
import random


class AddExamPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, callback=None, storage=None, close_callback=None, initial_date=None,
                 initial_time=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.callback = callback
        self.storage = storage
        self.close_callback = close_callback

        self.db_subjects = []
        self.subject_names = []
        self.semesters = []

        if self.storage:
            self.db_subjects = [dict(s) for s in self.storage.get_subjects()]
            self.subject_names = [s["name"] for s in self.db_subjects]
            self.semesters = [dict(s) for s in self.storage.get_semesters()]

        # KONTENER CENTRUJĄCY
        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(expand=True, fill="x", padx=30)

        self.center_box.grid_columnconfigure(0, weight=1)
        self.center_box.grid_columnconfigure(1, weight=2)

        # HEADER
        ctk.CTkLabel(self.center_box, text=self.txt.get("win_add_title", "Add New Exam"),
                     font=("Arial", 22, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # 1. PRZEDMIOT
        ctk.CTkLabel(self.center_box, text=self.txt["form_subject"]).grid(row=1, column=0, pady=10, padx=10, sticky="e")

        subj_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        subj_frame.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        self.combo_subject = ctk.CTkComboBox(subj_frame, values=self.subject_names,
                                             command=self.on_subject_change)
        self.combo_subject.pack(side="left", fill="x", expand=True)
        self.combo_subject.set("")

        self.btn_sem_filter = ctk.CTkButton(subj_frame, text="📅", width=35,
                                            fg_color="transparent", border_width=1, border_color="gray",
                                            text_color=("gray10", "gray90"),
                                            command=self.open_semester_menu)
        self.btn_sem_filter.pack(side="left", padx=(5, 0))

        # 2. TYP
        ctk.CTkLabel(self.center_box, text=self.txt["form_type"]).grid(row=2, column=0, pady=10, padx=10, sticky="e")
        self.entry_title = ctk.CTkEntry(self.center_box)
        self.entry_title.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # 3. DATA
        ctk.CTkLabel(self.center_box, text=self.txt["form_date"]).grid(row=3, column=0, pady=10, padx=10, sticky="e")

        date_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        date_frame.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        # TK Widget (DateEntry) stylizowany na ciemno
        self.entry_date = DateEntry(date_frame, width=15, date_pattern='y-mm-dd',
                                    background='#3a3a3a', foreground='white', borderwidth=0)
        self.entry_date.pack()

        # ZMIANA: Obsługa wstępnej daty
        if initial_date:
            try:
                self.entry_date.set_date(initial_date)
            except:
                pass

        # 4. CZAS
        ctk.CTkLabel(self.center_box, text=self.txt.get("form_time", "Time (HH:MM)")).grid(row=4, column=0, pady=10,
                                                                                           padx=10, sticky="e")
        self.entry_time = ctk.CTkEntry(self.center_box)

        # ZMIANA: Obsługa wstępnej godziny lub domyślnej
        default_time = initial_time if initial_time else "09:00"
        self.entry_time.insert(0, default_time)

        self.entry_time.grid(row=4, column=1, padx=10, pady=10, sticky="ew")

        # 5. BARIERA
        self.var_ignore_barrier = tk.BooleanVar(value=False)
        cb_text = self.txt.get("form_ignore_barrier", "Ignoruj w planowaniu (Bariera)")
        self.cb_barrier = ctk.CTkCheckBox(self.center_box, text=cb_text, variable=self.var_ignore_barrier,
                                          onvalue=True, offvalue=False)
        self.cb_barrier.grid(row=5, column=0, columnspan=2, pady=(20, 10))

        self.selected_color = None

        # 6. TEMATY
        ctk.CTkLabel(self.center_box, text=self.txt["form_topics_add"]).grid(row=6, column=0, pady=(10, 5),
                                                                             columnspan=2)

        self.text_topics = ctk.CTkTextbox(self.center_box, height=120)
        self.text_topics.grid(row=7, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="ew")

        # PRZYCISKI
        btn_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        btn_frame.grid(row=8, column=0, columnspan=2, pady=10)

        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save"], command=self.save_exam, **self.btn_style)
        btn_save.pack(side="left", padx=10)

        btn_cancel = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.perform_close, **self.btn_style)
        btn_cancel.pack(side="left", padx=10)
        btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

    def perform_close(self):
        if self.close_callback:
            self.close_callback()
        else:
            if hasattr(self, 'winfo_toplevel'):
                try:
                    self.winfo_toplevel().destroy()
                except:
                    pass

    def open_semester_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.txt.get("val_all", "All"),
                         command=lambda: self.filter_subjects_by_semester(None))
        menu.add_separator()
        sorted_semesters = sorted(self.semesters, key=lambda x: (not x["is_current"], x["start_date"]), reverse=True)
        for sem in sorted_semesters:
            label_text = sem["name"]
            if sem["is_current"]: label_text += f" ({self.txt.get('tag_current', 'Current')})"
            menu.add_command(label=label_text, command=lambda s_id=sem["id"]: self.filter_subjects_by_semester(s_id))
        try:
            x = self.btn_sem_filter.winfo_rootx()
            y = self.btn_sem_filter.winfo_rooty() + self.btn_sem_filter.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def filter_subjects_by_semester(self, semester_id):
        if semester_id is None:
            filtered_names = [s["name"] for s in self.db_subjects]
        else:
            filtered_names = [s["name"] for s in self.db_subjects if s["semester_id"] == semester_id]
        if not filtered_names: filtered_names = [""]
        self.combo_subject.configure(values=filtered_names)
        self.combo_subject.set("")

    def on_subject_change(self, choice):
        found = False
        for sub in self.db_subjects:
            if sub["name"] == choice:
                self.selected_color = sub["color"]
                found = True
                break
        if not found: self.selected_color = None

    def save_exam(self):
        subject_name = self.combo_subject.get().strip()
        title = self.entry_title.get().strip()
        date_val = self.entry_date.get()
        time_val = self.entry_time.get().strip()
        topics_raw = self.text_topics.get("0.0", "end").strip()

        if not subject_name or not title or not date_val:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_fill_fields"])
            return

        if not self.storage: return

        subject_id = None
        subject_color = self.selected_color

        for sub in self.db_subjects:
            if sub["name"] == subject_name:
                subject_id = sub["id"]
                if not subject_color: subject_color = sub["color"]
                break

        if not subject_id:
            random_colors = ["#e74c3c", "#8e44ad", "#3498db", "#1abc9c", "#f1c40f", "#e67e22", "#2ecc71"]
            subject_color = random.choice(random_colors)
            semesters = self.storage.get_semesters()
            semester_id = None
            if semesters:
                curr = [s for s in semesters if s["is_current"]]
                if curr:
                    semester_id = curr[0]["id"]
                else:
                    semester_id = semesters[0]["id"]
            else:
                semester_id = f"sem_{uuid.uuid4().hex[:8]}"
                self.storage.add_semester({
                    "id": semester_id, "name": "Default Semester",
                    "start_date": str(datetime.now().date()),
                    "end_date": str((datetime.now() + timedelta(days=180)).date()), "is_current": 1
                })
            subject_id = f"sub_{uuid.uuid4().hex[:8]}"
            short_name = subject_name[:3].upper()
            self.storage.add_subject({
                "id": subject_id, "semester_id": semester_id, "name": subject_name,
                "short_name": short_name, "color": subject_color, "weight": 1.0
            })

        exam_id = f"exam_{uuid.uuid4().hex[:8]}"
        new_exam = {
            "id": exam_id, "subject_id": subject_id, "subject": subject_name, "title": title,
            "date": date_val, "time": time_val, "note": "",
            "ignore_barrier": self.var_ignore_barrier.get(), "color": subject_color
        }
        self.storage.add_exam(new_exam)

        global_stats = self.storage.get_global_stats()
        curr_exams = global_stats.get("exams_added", 0)
        self.storage.update_global_stat("exams_added", curr_exams + 1)

        topics_list = [t.strip() for t in topics_raw.split('\n') if t.strip()]
        for topic in topics_list:
            new_topic = {
                "id": f"topic_{uuid.uuid4().hex[:8]}", "exam_id": exam_id, "name": topic,
                "status": "todo", "scheduled_date": None, "locked": False, "note": ""
            }
            self.storage.add_topic(new_topic)

        self.perform_close()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_added"].format(count=len(topics_list)))
        if self.callback: self.callback()