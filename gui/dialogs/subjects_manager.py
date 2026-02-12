from tkinter import messagebox, ttk
import customtkinter as ctk
from tkcalendar import DateEntry
import uuid
from gui.dialogs.color_picker import ColorPickerWindow


class SubjectsManagerWindow:
    def __init__(self, parent, txt, btn_style, storage, refresh_callback=None):
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.refresh_callback = refresh_callback

        self.current_semester_id = None
        self.semesters_data = []

        # GŁÓWNE OKNO
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_subj_man_title", "Subjects & Semesters Manager"))
        self.win.geometry("1000x700")
        self.win.minsize(900, 600)

        # UKŁAD GŁÓWNY
        self.win.columnconfigure(0, weight=3)  # Lewy (30%)
        self.win.columnconfigure(1, weight=7)  # Prawy (70%)
        self.win.rowconfigure(0, weight=1)

        # --- LEWY PANEL: SEMESTRY ---
        self.frame_left = ctk.CTkFrame(self.win, corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        self._init_left_panel()

        # --- PRAWY PANEL: PRZEDMIOTY ---
        self.frame_right = ctk.CTkFrame(self.win, corner_radius=0, fg_color="transparent")
        self.frame_right.grid(row=0, column=1, sticky="nsew")
        self._init_right_panel()

        # --- STOPKA Z PRZYCISKIEM ZAMKNIJ ---
        self.frame_footer = ctk.CTkFrame(self.win, height=40, corner_radius=0)
        self.frame_footer.grid(row=1, column=0, columnspan=2, sticky="ew")

        ctk.CTkButton(self.frame_footer, text=self.txt.get("btn_close", "Close"),
                      command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=20, pady=10)

        self.load_semesters()

    def _init_left_panel(self):
        ctk.CTkLabel(self.frame_left, text=self.txt.get("lbl_semesters", "Semesters"),
                     font=("Arial", 16, "bold")).pack(pady=10, padx=10, anchor="w")

        style = ttk.Style()
        style.configure("Treeview", rowheight=25)

        self.tree_sem = ttk.Treeview(self.frame_left, columns=("dates"), show="tree headings", selectmode="browse")
        self.tree_sem.heading("#0", text=self.txt.get("col_name", "Name"))
        self.tree_sem.column("#0", width=140)
        self.tree_sem.heading("dates", text=self.txt.get("col_dates", "Dates"))
        self.tree_sem.column("dates", width=100)

        current_mode = ctk.get_appearance_mode()
        active_color = "#0066cc" if current_mode == "Light" else "#3498db"
        self.tree_sem.tag_configure("current", foreground=active_color, font=("Arial", 11, "bold"))
        self.tree_sem.tag_configure("normal", font=("Arial", 11))

        self.tree_sem.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tree_sem.bind("<<TreeviewSelect>>", self.on_semester_select)

        btn_frame = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)

        row1 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        row1.pack(fill="x", pady=2)

        ctk.CTkButton(row1, text="+", width=30, command=self.add_semester, **self.btn_style).pack(side="left", padx=2)
        ctk.CTkButton(row1, text=self.txt.get("btn_edit", "Edit"), width=60, command=self.edit_semester,
                      **self.btn_style).pack(side="left", padx=2, fill="x", expand=True)

        del_style = self.btn_style.copy()
        del_style["fg_color"] = "#e74c3c"
        del_style["hover_color"] = "#c0392b"
        ctk.CTkButton(row1, text=self.txt.get("btn_delete", "Del"), width=40, command=self.delete_semester,
                      **del_style).pack(side="left", padx=2)

        ctk.CTkButton(btn_frame, text=self.txt.get("btn_set_current", "Set as Current"),
                      command=self.set_current_semester,
                      fg_color="transparent", border_width=1, border_color="gray",
                      text_color=("gray10", "gray90")).pack(fill="x", pady=(5, 0))

    def _init_right_panel(self):
        # Empty State
        self.frame_empty = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        ctk.CTkLabel(self.frame_empty, text="⬅", font=("Arial", 40)).pack(pady=(150, 10))
        ctk.CTkLabel(self.frame_empty,
                     text=self.txt.get("msg_select_sem_first", "Please select or add a semester first."),
                     font=("Arial", 14), text_color="gray").pack()

        # Content State
        self.frame_content = ctk.CTkFrame(self.frame_right, fg_color="transparent")

        header_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_current_sem_title = ctk.CTkLabel(header_frame, text="Subjects", font=("Arial", 20, "bold"))
        self.lbl_current_sem_title.pack(side="left")

        ctk.CTkButton(header_frame, text="+ " + self.txt.get("btn_add_subj", "Add Subject"),
                      command=self.add_subject, **self.btn_style).pack(side="right")

        # Tabela Przedmiotów
        style = ttk.Style()
        style.configure("Big.Treeview", font=("Arial", 13), rowheight=30)
        style.configure("Big.Treeview.Heading", font=("Arial", 11, "bold"))

        cols = ("code", "weight", "start", "end")
        self.tree_subj = ttk.Treeview(self.frame_content, columns=cols, show="tree headings", selectmode="browse",
                                      style="Big.Treeview")

        self.tree_subj.heading("#0", text=self.txt.get("col_name", "Subject"))
        self.tree_subj.column("#0", width=250)

        self.tree_subj.heading("code", text=self.txt.get("col_short", "Code"))
        self.tree_subj.column("code", width=80, anchor="center")

        self.tree_subj.heading("weight", text=self.txt.get("col_weight", "ECTS"))
        self.tree_subj.column("weight", width=80, anchor="center")

        self.tree_subj.heading("start", text=self.txt.get("col_start", "Start"))
        self.tree_subj.column("start", width=90, anchor="center")
        self.tree_subj.heading("end", text=self.txt.get("col_end", "End"))
        self.tree_subj.column("end", width=90, anchor="center")

        self.tree_subj.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_box = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        btn_box.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_edit", "Edit"), command=self.edit_subject, **self.btn_style).pack(
            side="left", padx=5)

        del_style = self.btn_style.copy()
        del_style["fg_color"] = "#e74c3c"
        del_style["hover_color"] = "#c0392b"
        ctk.CTkButton(btn_box, text=self.txt.get("btn_delete", "Delete"), command=self.delete_subject,
                      **del_style).pack(side="right", padx=5)

        self.show_right_panel(empty=True)

    def show_right_panel(self, empty=True):
        if empty:
            self.frame_content.pack_forget()
            self.frame_empty.pack(fill="both", expand=True)
        else:
            self.frame_empty.pack_forget()
            self.frame_content.pack(fill="both", expand=True)

    def load_semesters(self):
        for item in self.tree_sem.get_children(): self.tree_sem.delete(item)
        self.semesters_data = [dict(s) for s in self.storage.get_semesters()]
        self.semesters_data.sort(key=lambda x: (not x["is_current"], x["start_date"]), reverse=True)

        for sem in self.semesters_data:
            tag = "current" if sem["is_current"] else "normal"
            display = ("★ " + sem["name"]) if sem["is_current"] else sem["name"]
            self.tree_sem.insert("", "end", iid=sem["id"], text=display,
                                 values=(f"{sem['start_date']} : {sem['end_date']}",), tags=(tag,))

    def on_semester_select(self, event):
        selected = self.tree_sem.selection()
        if not selected:
            self.show_right_panel(True)
            self.current_semester_id = None
            return
        self.current_semester_id = selected[0]
        self.show_right_panel(False)
        self.load_subjects()
        sem = next((s for s in self.semesters_data if s["id"] == self.current_semester_id), None)
        if sem: self.lbl_current_sem_title.configure(text=sem["name"])

    # --- CRUD SEMESTRY (z odświeżaniem) ---
    def add_semester(self):
        cb = lambda: [self.load_semesters(), self.refresh_callback() if self.refresh_callback else None]
        AddSemesterWindow(self.win, self.txt, self.btn_style, self.storage, callback=cb)

    def edit_semester(self):
        sel = self.tree_sem.selection()
        if not sel: return
        sem = next((s for s in self.semesters_data if s["id"] == sel[0]), None)
        if sem:
            cb = lambda: [self.load_semesters(), self.refresh_callback() if self.refresh_callback else None]
            AddSemesterWindow(self.win, self.txt, self.btn_style, self.storage, sem, cb)

    def delete_semester(self):
        sel = self.tree_sem.selection()
        if not sel: return
        if messagebox.askyesno(self.txt["msg_warning"], self.txt.get("msg_confirm_del_sem", "Delete semester?")):
            self.storage.delete_semester(sel[0])
            self.load_semesters()
            self.show_right_panel(True)
            if self.refresh_callback: self.refresh_callback()

    def set_current_semester(self):
        sel = self.tree_sem.selection()
        if not sel: return
        for sem in self.semesters_data:
            is_cur = (sem["id"] == sel[0])
            if sem["is_current"] != is_cur:
                sem["is_current"] = is_cur
                self.storage.update_semester(sem)
        self.load_semesters()
        if self.refresh_callback: self.refresh_callback()

    def load_subjects(self):
        if not self.current_semester_id: return
        for item in self.tree_subj.get_children(): self.tree_subj.delete(item)

        subjects = [dict(s) for s in self.storage.get_subjects(self.current_semester_id)]
        for sub in subjects:
            # Kolorowanie w tabeli - jeśli None to domyślny czarny/biały z motywu
            # Tutaj używamy bezpiecznego koloru tylko do tagu, jeśli None to tag nie zadziała (będzie domyślny)
            safe_color = sub['color'] if sub.get('color') else ""
            if safe_color:
                self.tree_subj.tag_configure(f"col_{sub['id']}", foreground=safe_color)
                tags = (f"col_{sub['id']}",)
            else:
                tags = ()

            s_start = sub.get("start_datetime", "").split()[0] if sub.get("start_datetime") else ""
            s_end = sub.get("end_datetime", "").split()[0] if sub.get("end_datetime") else ""

            self.tree_subj.insert("", "end", iid=sub["id"], text=f"● {sub['name']}",
                                  values=(sub["short_name"], sub["weight"], s_start, s_end), tags=tags)

    # --- CRUD PRZEDMIOTY (z odświeżaniem) ---
    def add_subject(self):
        if not self.current_semester_id: return
        cb = lambda: [self.load_subjects(), self.refresh_callback() if self.refresh_callback else None]
        AddSubjectWindow(self.win, self.txt, self.btn_style, self.storage, self.current_semester_id, callback=cb)

    def edit_subject(self):
        sel = self.tree_subj.selection()
        if not sel: return
        subjects = [dict(s) for s in self.storage.get_subjects(self.current_semester_id)]
        sub = next((s for s in subjects if s["id"] == sel[0]), None)
        if sub:
            cb = lambda: [self.load_subjects(), self.refresh_callback() if self.refresh_callback else None]
            AddSubjectWindow(self.win, self.txt, self.btn_style, self.storage, self.current_semester_id, sub, cb)

    def delete_subject(self):
        sel = self.tree_subj.selection()
        if not sel: return
        if messagebox.askyesno(self.txt["msg_warning"], self.txt.get("msg_confirm_del_subj", "Delete subject?")):
            self.storage.delete_subject(sel[0])
            self.load_subjects()
            if self.refresh_callback: self.refresh_callback()


class AddSemesterWindow:
    def __init__(self, parent, txt, btn_style, storage, sem_data=None, callback=None):
        self.win = ctk.CTkToplevel(parent)
        self.txt = txt
        self.storage = storage
        self.sem_data = sem_data
        self.callback = callback

        self.win.title("Edit Semester" if sem_data else "Add Semester")
        self.win.geometry("350x300")

        ctk.CTkLabel(self.win, text=self.txt.get("form_name", "Name")).pack(pady=(10, 2))
        self.ent_name = ctk.CTkEntry(self.win)
        self.ent_name.pack(pady=5)
        if sem_data: self.ent_name.insert(0, sem_data["name"])

        f_date = ctk.CTkFrame(self.win, fg_color="transparent")
        f_date.pack(pady=10)

        ctk.CTkLabel(f_date, text=self.txt.get("form_start", "Start")).grid(row=0, column=0, padx=5)
        self.cal_start = DateEntry(f_date, width=12, date_pattern='y-mm-dd')
        self.cal_start.grid(row=1, column=0, padx=5)

        ctk.CTkLabel(f_date, text=self.txt.get("form_end", "End")).grid(row=0, column=1, padx=5)
        self.cal_end = DateEntry(f_date, width=12, date_pattern='y-mm-dd')
        self.cal_end.grid(row=1, column=1, padx=5)

        if sem_data:
            self.cal_start.set_date(sem_data["start_date"])
            self.cal_end.set_date(sem_data["end_date"])

        btn_box = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_box.pack(pady=20, fill="x")

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **btn_style).pack(side="left",
                                                                                                           padx=20,
                                                                                                           expand=True)
        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=20,
                                                                                                    expand=True)

    def save(self):
        name = self.ent_name.get()
        if not name: return
        data = {
            "id": self.sem_data["id"] if self.sem_data else f"sem_{uuid.uuid4().hex[:8]}",
            "name": name,
            "start_date": str(self.cal_start.get_date()),
            "end_date": str(self.cal_end.get_date()),
            "is_current": self.sem_data["is_current"] if self.sem_data else 0
        }
        if self.sem_data:
            self.storage.update_semester(data)
        else:
            self.storage.add_semester(data)
        if self.callback: self.callback()
        self.win.destroy()


class AddSubjectWindow:
    def __init__(self, parent, txt, btn_style, storage, semester_id, subject_data=None, callback=None):
        self.win = ctk.CTkToplevel(parent)
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.subject_data = subject_data
        self.current_semester_id = semester_id
        self.callback = callback

        self.schedule_entries = []
        if self.subject_data:
            raw = self.storage.get_schedule_entries_by_subject(self.subject_data["id"])
            self.schedule_entries = [dict(r) for r in raw]

        # FIX: Domyślny kolor to None (niebieski tylko jako fallback przy wyświetlaniu, ale nie tutaj)
        self.selected_color = subject_data["color"] if subject_data else None

        title = "Edit Subject" if subject_data else "Add Subject"
        self.win.title(title)
        self.win.geometry("500x700")

        # 1. NAZWA i SEMESTR
        f_top = ctk.CTkFrame(self.win, fg_color="transparent")
        f_top.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(f_top, text=self.txt.get("form_name", "Subject Name")).grid(row=0, column=0, sticky="w", padx=5)
        self.ent_name = ctk.CTkEntry(f_top, width=200)
        self.ent_name.grid(row=0, column=1, sticky="w", padx=5)
        if subject_data: self.ent_name.insert(0, subject_data["name"])

        # Semestr Change
        ctk.CTkLabel(f_top, text=self.txt.get("lbl_semester", "Semester")).grid(row=1, column=0, sticky="w", padx=5,
                                                                                pady=5)

        self.all_semesters = [dict(s) for s in self.storage.get_semesters()]
        sem_names = [s["name"] for s in self.all_semesters]
        self.combo_sem = ctk.CTkComboBox(f_top, values=sem_names)
        self.combo_sem.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        start_sem_id = subject_data["semester_id"] if subject_data else semester_id
        start_sem = next((s for s in self.all_semesters if s["id"] == start_sem_id), None)
        if start_sem: self.combo_sem.set(start_sem["name"])

        # 2. SKRÓT, WAGA, KOLOR
        f_opts = ctk.CTkFrame(self.win, fg_color="transparent")
        f_opts.pack(fill="x", padx=10)

        ctk.CTkLabel(f_opts, text="Short").pack(side="left", padx=5)
        self.ent_short = ctk.CTkEntry(f_opts, width=50)
        self.ent_short.pack(side="left", padx=5)
        if subject_data: self.ent_short.insert(0, subject_data["short_name"])

        ctk.CTkLabel(f_opts, text="ECTS").pack(side="left", padx=5)
        self.ent_weight = ctk.CTkEntry(f_opts, width=40)
        self.ent_weight.pack(side="left", padx=5)
        self.ent_weight.insert(0, str(subject_data["weight"]) if subject_data else "1.0")

        # FIX: Wizualizacja koloru na przycisku (jeśli None to szary)
        btn_disp_color = self.selected_color if self.selected_color else "gray"
        self.btn_color = ctk.CTkButton(f_opts, text="", width=30, height=28, fg_color=btn_disp_color,
                                       command=self.pick_color)
        self.btn_color.pack(side="left", padx=10)

        # 3. CZAS TRWANIA
        ctk.CTkFrame(self.win, height=2, fg_color="gray").pack(fill="x", padx=20, pady=5)

        f_dur = ctk.CTkFrame(self.win, fg_color="transparent")
        f_dur.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(f_dur, text="Start Date:").pack(side="left", padx=5)
        self.cal_start = DateEntry(f_dur, width=12, date_pattern='y-mm-dd')
        self.cal_start.pack(side="left", padx=5)

        ctk.CTkLabel(f_dur, text="End Date:").pack(side="left", padx=5)
        self.cal_end = DateEntry(f_dur, width=12, date_pattern='y-mm-dd')
        self.cal_end.pack(side="left", padx=5)

        if subject_data:
            if subject_data.get("start_datetime"):
                try:
                    self.cal_start.set_date(subject_data["start_datetime"].split()[0])
                except:
                    pass
            if subject_data.get("end_datetime"):
                try:
                    self.cal_end.set_date(subject_data["end_datetime"].split()[0])
                except:
                    pass
        else:
            if start_sem and start_sem.get("start_date") and start_sem.get("end_date"):
                try:
                    self.cal_start.set_date(start_sem["start_date"])
                    self.cal_end.set_date(start_sem["end_date"])
                except:
                    pass

        # 4. HARMONOGRAM
        ctk.CTkFrame(self.win, height=2, fg_color="gray").pack(fill="x", padx=20, pady=10)

        f_sched_head = ctk.CTkFrame(self.win, fg_color="transparent")
        f_sched_head.pack(fill="x", padx=10)
        ctk.CTkLabel(f_sched_head, text=self.txt.get("lbl_schedule", "Class Schedule"),
                     font=("Arial", 12, "bold")).pack(side="left")
        ctk.CTkButton(f_sched_head, text="+ Add Slot", width=80, height=24, command=self.add_slot).pack(side="right")

        self.tree_sched = ttk.Treeview(self.win, columns=("day", "time", "loc"), show="headings", height=5)
        self.tree_sched.heading("day", text="Day")
        self.tree_sched.column("day", width=80)
        self.tree_sched.heading("time", text="Time")
        self.tree_sched.column("time", width=100)
        self.tree_sched.heading("loc", text="Room/Type")
        self.tree_sched.column("loc", width=100)
        self.tree_sched.pack(fill="both", expand=True, padx=15, pady=5)

        ctk.CTkButton(self.win, text="Remove Selected Slot", fg_color="#e74c3c", hover_color="#c0392b", height=24,
                      command=self.remove_slot).pack(pady=5)

        self.refresh_schedule_list()

        # 5. PRZYCISKI
        btn_box = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_box.pack(pady=20, fill="x")

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **btn_style).pack(side="left",
                                                                                                           padx=20,
                                                                                                           expand=True)
        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=20,
                                                                                                    expand=True)

    def refresh_schedule_list(self):
        for item in self.tree_sched.get_children(): self.tree_sched.delete(item)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.schedule_entries.sort(key=lambda x: (x["day_of_week"], x["start_time"]))

        for idx, entry in enumerate(self.schedule_entries):
            d_name = days[entry["day_of_week"]]
            t_str = f"{entry['start_time']} - {entry['end_time']}"
            loc_str = f"{entry.get('room', '')} ({entry.get('type', '')})"
            self.tree_sched.insert("", "end", iid=str(idx), values=(d_name, t_str, loc_str))

    def add_slot(self):
        AddScheduleEntryWindow(self.win, self.txt, self.btn_style, callback=self.on_slot_added)

    def on_slot_added(self, new_entry):
        self.schedule_entries.append(new_entry)
        self.refresh_schedule_list()

    def remove_slot(self):
        sel = self.tree_sched.selection()
        if not sel: return
        idx = int(sel[0])
        del self.schedule_entries[idx]
        self.refresh_schedule_list()

    def pick_color(self):
        ColorPickerWindow(self.win, self.txt, self.selected_color,
                          lambda c: (setattr(self, 'selected_color', c), self.btn_color.configure(fg_color=c)))

    def save(self):
        name = self.ent_name.get()
        short = self.ent_short.get()
        if not name: return
        if not short: short = name[:3].upper()

        try:
            w = float(self.ent_weight.get())
        except:
            w = 1.0

        sem_name = self.combo_sem.get()
        target_sem = next((s for s in self.all_semesters if s["name"] == sem_name), None)
        sem_id = target_sem["id"] if target_sem else self.current_semester_id

        start_date = str(self.cal_start.get_date())
        end_date = str(self.cal_end.get_date())

        sub_id = self.subject_data["id"] if self.subject_data else f"sub_{uuid.uuid4().hex[:8]}"
        data = {
            "id": sub_id,
            "semester_id": sem_id,
            "name": name,
            "short_name": short,
            "color": self.selected_color,  # Tu przekazujemy None jeśli nie wybrano
            "weight": w,
            "start_datetime": start_date,
            "end_datetime": end_date
        }

        if self.subject_data:
            self.storage.update_subject(data)
        else:
            self.storage.add_subject(data)

        old_entries = self.storage.get_schedule_entries_by_subject(sub_id)
        for old in old_entries:
            self.storage.delete_schedule_entry(old["id"])

        for entry in self.schedule_entries:
            entry_id = f"sch_{uuid.uuid4().hex[:8]}"
            db_entry = {
                "id": entry_id,
                "subject_id": sub_id,
                "day_of_week": entry["day_of_week"],
                "start_time": entry["start_time"],
                "end_time": entry["end_time"],
                "room": entry["room"],
                "type": entry["type"],
                "period_start": None,
                "period_end": None
            }
            self.storage.add_schedule_entry(db_entry)

        if self.callback: self.callback()
        self.win.destroy()


class AddScheduleEntryWindow:
    def __init__(self, parent, txt, btn_style, callback):
        self.win = ctk.CTkToplevel(parent)
        self.txt = txt
        self.callback = callback
        self.win.title("Add Class Slot")
        self.win.geometry("300x350")

        ctk.CTkLabel(self.win, text="Day of Week").pack(pady=5)
        self.combo_day = ctk.CTkComboBox(self.win,
                                         values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
                                                 "Sunday"])
        self.combo_day.pack()

        f_time = ctk.CTkFrame(self.win, fg_color="transparent")
        f_time.pack(pady=10)
        ctk.CTkLabel(f_time, text="Start (HH:MM)").grid(row=0, column=0)
        ctk.CTkLabel(f_time, text="End (HH:MM)").grid(row=0, column=1)
        self.ent_start = ctk.CTkEntry(f_time, width=60, placeholder_text="08:00")
        self.ent_start.grid(row=1, column=0, padx=5)
        self.ent_end = ctk.CTkEntry(f_time, width=60, placeholder_text="09:30")
        self.ent_end.grid(row=1, column=1, padx=5)

        ctk.CTkLabel(self.win, text="Room").pack()
        self.ent_room = ctk.CTkEntry(self.win)
        self.ent_room.pack(pady=2)

        ctk.CTkLabel(self.win, text="Type (Lecture/Lab)").pack()
        self.ent_type = ctk.CTkComboBox(self.win, values=["Lecture", "Lab", "Seminar", "Exam"])
        self.ent_type.pack(pady=2)

        btn_box = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_box.pack(pady=20, fill="x")
        ctk.CTkButton(btn_box, text="Add", command=self.save, **btn_style).pack(side="left", padx=20, expand=True)
        ctk.CTkButton(btn_box, text="Cancel", command=self.win.destroy, fg_color="transparent", border_width=1,
                      text_color=("gray10", "gray90")).pack(side="right", padx=20, expand=True)

    def save(self):
        day_str = self.combo_day.get()
        days_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}

        entry = {
            "day_of_week": days_map.get(day_str, 0),
            "start_time": self.ent_start.get(),
            "end_time": self.ent_end.get(),
            "room": self.ent_room.get(),
            "type": self.ent_type.get()
        }
        self.callback(entry)
        self.win.destroy()