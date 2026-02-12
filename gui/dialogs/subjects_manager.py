import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from tkcalendar import DateEntry
import uuid
from gui.dialogs.color_picker import ColorPickerWindow


class SubjectsManagerPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, refresh_callback=None, close_callback=None, drawer=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.refresh_callback = refresh_callback
        self.close_callback = close_callback
        self.drawer = drawer

        self.current_semester_id = None
        self.semesters_data = []

        # UKŁAD GŁÓWNY
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- HEADER ---
        self.header = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.header, text=self.txt.get("win_subj_man_title", "Subjects & Semesters Manager"),
                     font=("Arial", 20, "bold")).pack(side="left")

        # --- RAMKA Z BIAŁYM OBRAMOWANIEM ---
        self.border_frame = ctk.CTkFrame(self, fg_color="transparent",
                                         border_width=1, border_color=("gray70", "white"), corner_radius=0)
        self.border_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # --- PANED WINDOW (ROZCIĄGLIWY PODZIAŁ) ---
        self.paned = tk.PanedWindow(self.border_frame, orient="horizontal", sashwidth=6, bg="#2b2b2b", bd=0)
        self.paned.pack(fill="both", expand=True, padx=2, pady=2)

        # --- LEWY PANEL: SEMESTRY ---
        self.frame_left = ctk.CTkFrame(self.paned, corner_radius=0, fg_color="transparent")
        self.paned.add(self.frame_left, minsize=250, stretch="always")

        self._init_left_panel()

        # --- PRAWY PANEL: PRZEDMIOTY ---
        self.frame_right = ctk.CTkFrame(self.paned, corner_radius=0, fg_color="transparent")
        self.paned.add(self.frame_right, minsize=400, stretch="always")

        self._init_right_panel()

        # --- STOPKA ---
        self.frame_footer = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="transparent")
        self.frame_footer.grid(row=2, column=0, sticky="ew")

        ctk.CTkButton(self.frame_footer, text=self.txt.get("btn_close", "Back"),
                      command=self.perform_close,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      height=32, corner_radius=20).pack(side="right", padx=20, pady=10)

        self.load_semesters()

    def perform_close(self):
        if self.close_callback:
            self.close_callback()
        elif hasattr(self, 'winfo_toplevel'):
            try:
                self.winfo_toplevel().destroy()
            except:
                pass

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
                      text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                      height=32, corner_radius=20).pack(fill="x", pady=(5, 0))

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

    # --- CRUD SEMESTRY (SZUFLADA) ---
    def add_semester(self):
        cb = lambda: [self.load_semesters(), self.refresh_callback() if self.refresh_callback else None]
        if self.drawer:
            self.drawer.set_content(AddSemesterPanel, txt=self.txt, btn_style=self.btn_style,
                                    storage=self.storage, callback=cb, close_callback=self.drawer.close_panel)

    def edit_semester(self):
        sel = self.tree_sem.selection()
        if not sel: return
        sem = next((s for s in self.semesters_data if s["id"] == sel[0]), None)
        if sem:
            cb = lambda: [self.load_semesters(), self.refresh_callback() if self.refresh_callback else None]
            if self.drawer:
                self.drawer.set_content(AddSemesterPanel, txt=self.txt, btn_style=self.btn_style,
                                        storage=self.storage, sem_data=sem, callback=cb,
                                        close_callback=self.drawer.close_panel)

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

    # --- CRUD PRZEDMIOTY (SZUFLADA) ---
    def add_subject(self):
        if not self.current_semester_id: return
        cb = lambda: [self.load_subjects(), self.refresh_callback() if self.refresh_callback else None]
        if self.drawer:
            self.drawer.set_content(AddSubjectPanel, txt=self.txt, btn_style=self.btn_style,
                                    storage=self.storage, semester_id=self.current_semester_id,
                                    callback=cb, close_callback=self.drawer.close_panel)

    def edit_subject(self):
        sel = self.tree_subj.selection()
        if not sel: return
        subjects = [dict(s) for s in self.storage.get_subjects(self.current_semester_id)]
        sub = next((s for s in subjects if s["id"] == sel[0]), None)
        if sub:
            cb = lambda: [self.load_subjects(), self.refresh_callback() if self.refresh_callback else None]
            if self.drawer:
                self.drawer.set_content(AddSubjectPanel, txt=self.txt, btn_style=self.btn_style,
                                        storage=self.storage, semester_id=self.current_semester_id,
                                        subject_data=sub, callback=cb, close_callback=self.drawer.close_panel)

    def delete_subject(self):
        sel = self.tree_subj.selection()
        if not sel: return
        if messagebox.askyesno(self.txt["msg_warning"], self.txt.get("msg_confirm_del_subj", "Delete subject?")):
            self.storage.delete_subject(sel[0])
            self.load_subjects()
            if self.refresh_callback: self.refresh_callback()


class AddSemesterPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, sem_data=None, callback=None, close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.sem_data = sem_data
        self.callback = callback
        self.close_callback = close_callback

        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(expand=True, fill="x", padx=30)
        self.center_box.grid_columnconfigure(0, weight=1)
        self.center_box.grid_columnconfigure(1, weight=2)

        title = "Edit Semester" if sem_data else "Add Semester"
        ctk.CTkLabel(self.center_box, text=title, font=("Arial", 20, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                   pady=(0, 20))

        ctk.CTkLabel(self.center_box, text=self.txt.get("form_name", "Name")).grid(row=1, column=0, pady=10, sticky="e",
                                                                                   padx=10)
        self.ent_name = ctk.CTkEntry(self.center_box)
        self.ent_name.grid(row=1, column=1, pady=10, sticky="ew", padx=10)
        if sem_data: self.ent_name.insert(0, sem_data["name"])

        ctk.CTkLabel(self.center_box, text=self.txt.get("form_start", "Start")).grid(row=2, column=0, pady=10,
                                                                                     sticky="e", padx=10)

        f_start = ctk.CTkFrame(self.center_box, fg_color="transparent")
        f_start.grid(row=2, column=1, sticky="w", padx=10)
        self.cal_start = DateEntry(f_start, width=15, date_pattern='y-mm-dd', background='#3a3a3a', foreground='white',
                                   borderwidth=0)
        self.cal_start.pack()

        ctk.CTkLabel(self.center_box, text=self.txt.get("form_end", "End")).grid(row=3, column=0, pady=10, sticky="e",
                                                                                 padx=10)

        f_end = ctk.CTkFrame(self.center_box, fg_color="transparent")
        f_end.grid(row=3, column=1, sticky="w", padx=10)
        self.cal_end = DateEntry(f_end, width=15, date_pattern='y-mm-dd', background='#3a3a3a', foreground='white',
                                 borderwidth=0)
        self.cal_end.pack()

        if sem_data:
            self.cal_start.set_date(sem_data["start_date"])
            self.cal_end.set_date(sem_data["end_date"])

        btn_box = ctk.CTkFrame(self.center_box, fg_color="transparent")
        btn_box.grid(row=4, column=0, columnspan=2, pady=30)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **self.btn_style).pack(
            side="left", padx=10)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.perform_close,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      height=32, corner_radius=20, font=("Arial", 13, "bold"), border_color="gray",
                      hover_color=("gray80", "gray30")).pack(side="left", padx=10)

    def perform_close(self):
        if self.close_callback: self.close_callback()

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
        self.perform_close()


class AddSubjectPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, semester_id, subject_data=None, callback=None,
                 close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.subject_data = subject_data
        self.current_semester_id = semester_id
        self.callback = callback
        self.close_callback = close_callback

        self.schedule_entries = []
        if self.subject_data:
            raw = self.storage.get_schedule_entries_by_subject(self.subject_data["id"])
            self.schedule_entries = [dict(r) for r in raw]

        self.selected_color = subject_data["color"] if subject_data else None

        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(expand=True, fill="x", padx=30)
        self.center_box.grid_columnconfigure(0, weight=1)
        self.center_box.grid_columnconfigure(1, weight=2)

        title = "Edit Subject" if subject_data else "Add Subject"
        ctk.CTkLabel(self.center_box, text=title, font=("Arial", 20, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                   pady=(0, 20))

        ctk.CTkLabel(self.center_box, text=self.txt.get("form_name", "Subject Name")).grid(row=1, column=0, sticky="e",
                                                                                           padx=10, pady=5)
        self.ent_name = ctk.CTkEntry(self.center_box)
        self.ent_name.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        if subject_data: self.ent_name.insert(0, subject_data["name"])

        ctk.CTkLabel(self.center_box, text=self.txt.get("lbl_semester", "Semester")).grid(row=2, column=0, sticky="e",
                                                                                          padx=10, pady=5)

        self.all_semesters = [dict(s) for s in self.storage.get_semesters()]
        sem_names = [s["name"] for s in self.all_semesters]
        self.combo_sem = ctk.CTkComboBox(self.center_box, values=sem_names)
        self.combo_sem.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        start_sem_id = subject_data["semester_id"] if subject_data else semester_id
        start_sem = next((s for s in self.all_semesters if s["id"] == start_sem_id), None)
        if start_sem: self.combo_sem.set(start_sem["name"])

        opts_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        opts_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ctk.CTkLabel(opts_frame, text="Short:").pack(side="left", padx=5)
        self.ent_short = ctk.CTkEntry(opts_frame, width=60)
        self.ent_short.pack(side="left", padx=5)
        if subject_data: self.ent_short.insert(0, subject_data["short_name"])

        ctk.CTkLabel(opts_frame, text="ECTS:").pack(side="left", padx=5)
        self.ent_weight = ctk.CTkEntry(opts_frame, width=50)
        self.ent_weight.pack(side="left", padx=5)
        self.ent_weight.insert(0, str(subject_data["weight"]) if subject_data else "1.0")

        btn_disp_color = self.selected_color if self.selected_color else "gray"
        self.btn_color = ctk.CTkButton(opts_frame, text="", width=30, height=28, fg_color=btn_disp_color,
                                       command=self.pick_color)
        self.btn_color.pack(side="left", padx=10)

        dates_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        dates_frame.grid(row=4, column=0, columnspan=2, pady=5)

        ctk.CTkLabel(dates_frame, text="Start:").pack(side="left", padx=5)
        f_d1 = ctk.CTkFrame(dates_frame, fg_color="transparent")
        f_d1.pack(side="left")
        self.cal_start = DateEntry(f_d1, width=12, date_pattern='y-mm-dd', background='#3a3a3a', foreground='white',
                                   borderwidth=0)
        self.cal_start.pack()

        ctk.CTkLabel(dates_frame, text="End:").pack(side="left", padx=5)
        f_d2 = ctk.CTkFrame(dates_frame, fg_color="transparent")
        f_d2.pack(side="left")
        self.cal_end = DateEntry(f_d2, width=12, date_pattern='y-mm-dd', background='#3a3a3a', foreground='white',
                                 borderwidth=0)
        self.cal_end.pack()

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

        sched_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        sched_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

        ctk.CTkLabel(sched_frame, text=self.txt.get("lbl_schedule", "Class Schedule"),
                     font=("Arial", 12, "bold")).pack(side="left")
        ctk.CTkButton(sched_frame, text="+ Slot", width=60, height=24, command=self.add_slot).pack(side="right")

        self.tree_sched = ttk.Treeview(self.center_box, columns=("day", "time", "loc"), show="headings", height=4)
        self.tree_sched.heading("day", text="Day")
        self.tree_sched.column("day", width=80)
        self.tree_sched.heading("time", text="Time")
        self.tree_sched.column("time", width=100)
        self.tree_sched.heading("loc", text="Room/Type")
        self.tree_sched.column("loc", width=100)
        self.tree_sched.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10)

        ctk.CTkButton(self.center_box, text="Remove Selected Slot", fg_color="#e74c3c", hover_color="#c0392b",
                      height=24,
                      command=self.remove_slot).grid(row=7, column=0, columnspan=2, pady=5)

        self.refresh_schedule_list()

        btn_box = ctk.CTkFrame(self.center_box, fg_color="transparent")
        btn_box.grid(row=8, column=0, columnspan=2, pady=20)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **self.btn_style).pack(
            side="left", padx=10)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.perform_close,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      height=32, corner_radius=20, font=("Arial", 13, "bold"), border_color="gray",
                      hover_color=("gray80", "gray30")).pack(side="left", padx=10)

    def perform_close(self):
        if self.close_callback: self.close_callback()

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
        AddScheduleEntryPopup(self, self.txt, self.btn_style, callback=self.on_slot_added)

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
        ColorPickerWindow(self.winfo_toplevel(), self.txt, self.selected_color,
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
            "id": sub_id, "semester_id": sem_id, "name": name, "short_name": short,
            "color": self.selected_color, "weight": w, "start_datetime": start_date, "end_datetime": end_date
        }

        if self.subject_data:
            self.storage.update_subject(data)
        else:
            self.storage.add_subject(data)

        old_entries = self.storage.get_schedule_entries_by_subject(sub_id)
        for old in old_entries: self.storage.delete_schedule_entry(old["id"])

        for entry in self.schedule_entries:
            entry_id = f"sch_{uuid.uuid4().hex[:8]}"
            db_entry = {
                "id": entry_id, "subject_id": sub_id, "day_of_week": entry["day_of_week"],
                "start_time": entry["start_time"], "end_time": entry["end_time"], "room": entry["room"],
                "type": entry["type"], "period_start": None, "period_end": None
            }
            self.storage.add_schedule_entry(db_entry)

        if self.callback: self.callback()
        self.perform_close()


class AddScheduleEntryPopup:
    def __init__(self, parent_widget, txt, btn_style, callback):
        self.parent = parent_widget
        self.txt = txt
        self.callback = callback

        # Toplevel bez systemowej belki (overrideredirect usunięte dla kompatybilności z MacOS, ale stylem udajemy)
        self.win = ctk.CTkToplevel(self.parent)
        self.win.title("Add Slot")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        # FIX: Transient dla focusu
        try:
            self.win.transient(self.parent.winfo_toplevel())
        except:
            pass
        self.win.lift()
        self.win.focus_force()
        self.win.grab_set()  # Modalność - blokuje klikanie pod spód
        self.win.configure(fg_color="#2b2b2b")

        w = 280
        h = 350

        try:
            # Pozycjonowanie obok szuflady
            drawer_x = self.parent.winfo_rootx()
            drawer_y = self.parent.winfo_rooty()
            pos_x = drawer_x - w - 10
            pos_y = drawer_y + 100
            self.win.geometry(f"{w}x{h}+{pos_x}+{pos_y}")
        except:
            self.win.geometry(f"{w}x{h}")

        border = ctk.CTkFrame(self.win, fg_color="transparent", border_width=2, border_color="gray")
        border.pack(fill="both", expand=True)

        ctk.CTkLabel(border, text="Add Class Slot", font=("Arial", 16, "bold")).pack(pady=10)

        ctk.CTkLabel(border, text="Day of Week").pack(pady=2)
        self.combo_day = ctk.CTkComboBox(border, width=200,
                                         values=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
                                                 "Sunday"])
        self.combo_day.pack(pady=2)

        f_time = ctk.CTkFrame(border, fg_color="transparent")
        f_time.pack(pady=5)
        ctk.CTkLabel(f_time, text="Start").grid(row=0, column=0, padx=5)
        ctk.CTkLabel(f_time, text="End").grid(row=0, column=1, padx=5)
        self.ent_start = ctk.CTkEntry(f_time, width=80, placeholder_text="08:00")
        self.ent_start.grid(row=1, column=0, padx=5)
        self.ent_end = ctk.CTkEntry(f_time, width=80, placeholder_text="09:30")
        self.ent_end.grid(row=1, column=1, padx=5)

        ctk.CTkLabel(border, text="Room / Type").pack(pady=2)
        self.ent_room = ctk.CTkEntry(border, width=200, placeholder_text="Room 101")
        self.ent_room.pack(pady=2)

        self.ent_type = ctk.CTkComboBox(border, width=200, values=["Lecture", "Lab", "Seminar", "Exam"])
        self.ent_type.pack(pady=5)

        btn_box = ctk.CTkFrame(border, fg_color="transparent")
        btn_box.pack(pady=20, fill="x", side="bottom")

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **btn_style).pack(side="left",
                                                                                                           padx=15,
                                                                                                           expand=True)

        # FIX: Manualny styl Cancel
        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      hover_color=("gray80", "gray30")).pack(side="right", padx=15, expand=True)

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