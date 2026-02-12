import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, date
import uuid


class GradesPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, close_callback=None, drawer=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.close_callback = close_callback
        self.drawer = drawer

        self.current_semester_id = None
        self.semesters = []
        self.subjects_data = []
        self.current_subject_id = None

        settings = self.storage.get_settings().get("grading_system", {})
        self.grade_mode = settings.get("grade_mode", "percentage")
        self.weight_mode = settings.get("weight_mode", "percentage")
        self.is_advanced = settings.get("advanced_mode", False)
        defaults_thresholds = {"3.0": 50, "3.5": 60, "4.0": 70, "4.5": 80, "5.0": 90}
        self.thresholds = settings.get("thresholds", defaults_thresholds)

        # UKŁAD GŁÓWNY
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # HEADER
        self.header = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(10, 0))

        ctk.CTkLabel(self.header, text=self.txt.get("win_grades_title", "Grades Manager"),
                     font=("Arial", 20, "bold")).pack(side="left")

        # --- RAMKA Z BIAŁYM OBRAMOWANIEM ---
        self.border_frame = ctk.CTkFrame(self, fg_color="transparent",
                                         border_width=1, border_color=("gray70", "white"), corner_radius=0)
        self.border_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # --- PANED WINDOW ---
        self.paned = tk.PanedWindow(self.border_frame, orient="horizontal", sashwidth=6, bg="#2b2b2b", bd=0)
        self.paned.pack(fill="both", expand=True, padx=2, pady=2)

        # LEWY PANEL
        self.frame_left = ctk.CTkFrame(self.paned, corner_radius=0, fg_color="transparent")
        self.paned.add(self.frame_left, minsize=250, stretch="always")

        self._init_left_panel()

        # PRAWY PANEL
        self.frame_right = ctk.CTkFrame(self.paned, corner_radius=0, fg_color="transparent")
        self.paned.add(self.frame_right, minsize=400, stretch="always")

        self._init_right_panel()

        # STOPKA
        self.frame_footer = ctk.CTkFrame(self, height=40, corner_radius=0, fg_color="transparent")
        self.frame_footer.grid(row=2, column=0, sticky="ew")

        ctk.CTkButton(self.frame_footer, text=self.txt.get("btn_close", "Back"), command=self.perform_close,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      hover_color=("gray80", "gray30"),
                      height=32, corner_radius=20).pack(side="right", padx=20, pady=10)

        self.load_data()

    def perform_close(self):
        if self.close_callback:
            self.close_callback()
        elif hasattr(self, 'winfo_toplevel'):
            try:
                self.winfo_toplevel().destroy()
            except:
                pass

    def _init_left_panel(self):
        self.top_left = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.top_left.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(self.top_left, text=self.txt.get("lbl_semester", "Semester"), font=("Arial", 12, "bold")).pack(
            anchor="w")
        self.combo_sem = ctk.CTkComboBox(self.top_left, command=self.on_semester_change)
        self.combo_sem.pack(fill="x", pady=(5, 5))

        self.lbl_sem_gpa = ctk.CTkLabel(self.top_left, text=self.txt.get("lbl_gpa_placeholder", "GPA: --"),
                                        font=("Arial", 14, "bold"), text_color="#2ecc71")
        self.lbl_sem_gpa.pack(anchor="w", pady=(0, 10))

        self.scroll_subjects = ctk.CTkScrollableFrame(self.frame_left, fg_color="transparent")
        self.scroll_subjects.pack(fill="both", expand=True, padx=5, pady=5)

    def _init_right_panel(self):
        # Stan pusty (brak wybranego przedmiotu)
        self.frame_empty = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        ctk.CTkLabel(self.frame_empty, text=self.txt.get("lbl_select_subject", "Select a subject to view grades"),
                     font=("Arial", 20)).pack(pady=(150, 10))

        # Stan z zawartością
        self.frame_content = ctk.CTkFrame(self.frame_right, fg_color="transparent")

        # Nagłówek przedmiotu
        header_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_subj_title = ctk.CTkLabel(header_frame, text=self.txt.get("lbl_subject", "Subject"),
                                           font=("Arial", 22, "bold"))
        self.lbl_subj_title.pack(side="left")

        self.lbl_subj_avg = ctk.CTkLabel(header_frame, text=self.txt.get("lbl_avg_placeholder", "Avg: --"),
                                         font=("Arial", 18, "bold"), text_color="#3498db")
        self.lbl_subj_avg.pack(side="left", padx=20)

        # Przyciski akcji (Góra)
        if self.is_advanced:
            ctk.CTkButton(header_frame, text=self.txt.get("btn_add_module", "+ Module"), width=80, fg_color="#e67e22",
                          hover_color="#d35400",
                          command=self.add_module).pack(side="right", padx=5)

        ctk.CTkButton(header_frame, text=self.txt.get("btn_add_grade", "+ Grade"), width=80, command=self.add_grade,
                      **self.btn_style).pack(side="right", padx=5)

        # Tabela (Treeview)
        style = ttk.Style()
        style.configure("Grades.Treeview", font=("Arial", 13), rowheight=30)
        style.configure("Grades.Treeview.Heading", font=("Arial", 13, "bold"), rowheight=30)

        cols = ("weight", "grade", "date")
        self.tree = ttk.Treeview(self.frame_content, columns=cols, show="tree headings", selectmode="browse",
                                 style="Grades.Treeview")

        self.tree.heading("#0", text=self.txt.get("col_desc", "Description"), anchor="w")
        self.tree.column("#0", width=300)

        self.tree.heading("weight", text=self.txt.get("col_weight_val", "Weight"))
        self.tree.column("weight", width=100, anchor="center")

        self.tree.heading("grade", text=self.txt.get("col_grade", "Grade"))
        self.tree.column("grade", width=100, anchor="center")

        self.tree.heading("date", text=self.txt.get("col_date", "Date"))
        self.tree.column("date", width=120, anchor="center")

        self.tree.tag_configure("module", font=("Arial", 13, "bold"), foreground="")
        self.tree.tag_configure("grade", font=("Arial", 13))

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Przyciski akcji (Dół)
        btn_box = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        btn_box.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_edit", "Edit"), command=self.edit_item, width=80,
                      **self.btn_style).pack(side="left", padx=5)
        ctk.CTkButton(btn_box, text=self.txt.get("btn_delete", "Delete"), command=self.delete_item, width=80,
                      fg_color="#e74c3c", hover_color="#c0392b").pack(side="right", padx=5)

        self.show_right_panel(empty=True)

    def show_right_panel(self, empty=True):
        if empty:
            self.frame_content.pack_forget()
            self.frame_empty.pack(fill="both", expand=True)
        else:
            self.frame_empty.pack_forget()
            self.frame_content.pack(fill="both", expand=True)

    def load_data(self):
        self.semesters = [dict(s) for s in self.storage.get_semesters()]
        self.semesters.sort(key=lambda x: (not x["is_current"], x["start_date"]), reverse=True)

        sem_names = [s["name"] for s in self.semesters]
        self.combo_sem.configure(values=sem_names)

        if self.semesters:
            if not self.current_semester_id:
                self.current_semester_id = self.semesters[0]["id"]
                self.combo_sem.set(self.semesters[0]["name"])
            self.refresh_subjects_list()
        else:
            self.combo_sem.set("")

    def on_semester_change(self, choice):
        sem = next((s for s in self.semesters if s["name"] == choice), None)
        if sem:
            self.current_semester_id = sem["id"]
            self.refresh_subjects_list()
            self.show_right_panel(empty=True)
            self.current_subject_id = None

    def refresh_subjects_list(self):
        for w in self.scroll_subjects.winfo_children():
            w.destroy()

        if not self.current_semester_id:
            return

        self.subjects_data = [dict(s) for s in self.storage.get_subjects(self.current_semester_id)]

        for sub in self.subjects_data:
            final_percent = self._calculate_final_percentage(sub["id"])

            avg_txt = self.txt.get("lbl_avg_placeholder", "Avg: --")

            if final_percent is None:
                avg_str = avg_txt
            else:
                avg_str = f"{final_percent:.1f}%"
                grade = self._percent_to_grade(final_percent)
                avg_str += f" ({grade})"

            color = sub.get("color")
            if not color: color = "gray"

            btn = ctk.CTkButton(self.scroll_subjects,
                                text=f"{sub['name']}\n{avg_str}",
                                height=55,
                                fg_color="transparent",
                                border_color=color,
                                border_width=2,
                                text_color=("gray10", "gray90"),
                                hover_color=("gray85", "gray25"),
                                command=lambda s=sub: self.open_subject(s))
            btn.pack(fill="x", pady=4)

        self._update_semester_gpa()

    def open_subject(self, subject):
        self.current_subject_id = subject["id"]
        color = subject.get("color")
        if not color: color = "gray"

        self.lbl_subj_title.configure(text=subject["name"], text_color=color)
        self.show_right_panel(empty=False)
        self.refresh_tree()

    def refresh_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self.current_subject_id: return

        raw_grades = [dict(g) for g in self.storage.get_grades(self.current_subject_id)]

        if self.is_advanced:
            modules = [dict(m) for m in self.storage.get_grade_modules(self.current_subject_id)]
            grouped = {m["id"]: [] for m in modules}
            ungrouped = []

            for g in raw_grades:
                mid = g.get("module_id")
                if mid and mid in grouped:
                    grouped[mid].append(g)
                else:
                    ungrouped.append(g)

            for mod in modules:
                mod_avg = self._calculate_module_avg(grouped[mod["id"]])
                avg_val_txt = f"{mod_avg:.1f}%" if mod_avg is not None else "--"
                avg_label = self.txt.get("lbl_avg_short", "Avg")

                mid = self.tree.insert("", "end", iid=mod["id"], text=f"{mod['name']}",
                                       values=(f"{mod['weight']}%", f"{avg_label}: {avg_val_txt}", ""), open=True,
                                       tags=("module",))
                for g in grouped[mod["id"]]: self._insert_grade_row(mid, g)

            if ungrouped:
                gen_name = self.txt.get("cat_general", "General / Uncategorized")
                gen_id = self.tree.insert("", "end", iid="general", text=gen_name,
                                          values=("??", "", ""), open=True, tags=("module",))
                for g in ungrouped: self._insert_grade_row(gen_id, g)

        else:
            for g in raw_grades: self._insert_grade_row("", g)

        final_percent = self._calculate_final_percentage(self.current_subject_id)
        avg_label = self.txt.get("lbl_avg_short", "Avg")

        if final_percent is not None:
            grade = self._percent_to_grade(final_percent)
            self.lbl_subj_avg.configure(text=f"{avg_label}: {final_percent:.1f}% -> {grade}")
        else:
            self.lbl_subj_avg.configure(text=f"{avg_label}: --")

    def _insert_grade_row(self, parent_id, g):
        val_str = f"{g['value']}"
        if self.grade_mode == "percentage": val_str += "%"
        w_str = f"{g['weight']}"
        if self.weight_mode == "percentage": w_str += "%"
        desc = g.get("desc") or self.txt.get("lbl_no_desc", "No desc")
        self.tree.insert(parent_id, "end", iid=g["id"], text=desc,
                         values=(w_str, val_str, g.get("date", "")), tags=("grade",))

    def _calculate_module_avg(self, grades):
        if not grades: return None
        total_w = 0
        weighted_sum = 0
        for g in grades:
            val = g["value"]
            w = g["weight"]
            weighted_sum += val * w
            total_w += w
        if total_w == 0: return 0
        return weighted_sum / total_w

    def _calculate_final_percentage(self, subject_id):
        if self.is_advanced:
            modules = [dict(m) for m in self.storage.get_grade_modules(subject_id)]
            all_grades = [dict(g) for g in self.storage.get_grades(subject_id)]
            total_score = 0
            total_module_weight = 0
            has_any_grade = False

            for mod in modules:
                mod_grades = [g for g in all_grades if g.get("module_id") == mod["id"]]
                mod_avg = self._calculate_module_avg(mod_grades)
                if mod_avg is not None:
                    has_any_grade = True
                    weight = mod["weight"]
                    total_score += mod_avg * (weight / 100.0)
                    total_module_weight += weight

            if not has_any_grade and total_module_weight == 0: return None
            return total_score
        else:
            grades = [dict(g) for g in self.storage.get_grades(subject_id)]
            return self._calculate_module_avg(grades)

    def _percent_to_grade(self, percent):
        if percent is None: return None
        sorted_thresholds = sorted([(k, v) for k, v in self.thresholds.items()], key=lambda x: x[1], reverse=True)
        for grade, threshold in sorted_thresholds:
            if percent >= threshold: return float(grade)
        return 2.0

    def _update_semester_gpa(self):
        gpa_txt = self.txt.get("lbl_gpa_placeholder", "GPA: --")
        if not self.subjects_data:
            self.lbl_sem_gpa.configure(text=gpa_txt)
            return

        total_ects = 0
        weighted_sum = 0
        valid_subjects = 0

        for sub in self.subjects_data:
            final_percent = self._calculate_final_percentage(sub["id"])
            if final_percent is None: continue
            grade_val = self._percent_to_grade(final_percent)
            ects = sub.get("weight", 0)
            weighted_sum += grade_val * ects
            total_ects += ects
            valid_subjects += 1

        if total_ects == 0 or valid_subjects == 0:
            self.lbl_sem_gpa.configure(text=gpa_txt)
        else:
            gpa = weighted_sum / total_ects
            lbl_gpa = self.txt.get("lbl_gpa", "GPA")
            self.lbl_sem_gpa.configure(text=f"{lbl_gpa}: {gpa:.2f}")

    # --- AKCJE CRUD (SZUFLADA) ---

    def add_module(self):
        if not self.current_subject_id: return
        cb = lambda: [self.refresh_tree(), self.refresh_subjects_list()]
        if self.drawer:
            self.drawer.set_content(AddModulePanel, txt=self.txt, btn_style=self.btn_style,
                                    storage=self.storage, subject_id=self.current_subject_id,
                                    callback=cb, close_callback=self.drawer.close_panel)

    def add_grade(self):
        if not self.current_subject_id:
            messagebox.showinfo(self.txt.get("title_info", "Info"),
                                self.txt.get("msg_select_subj", "Select a subject first."))
            return

        modules = []
        if self.is_advanced:
            modules = [dict(m) for m in self.storage.get_grade_modules(self.current_subject_id)]

        cb = lambda: [self.refresh_tree(), self.refresh_subjects_list()]
        if self.drawer:
            self.drawer.set_content(AddGradePanel, txt=self.txt, btn_style=self.btn_style,
                                    storage=self.storage, subject_id=self.current_subject_id,
                                    grade_mode=self.grade_mode, weight_mode=self.weight_mode,
                                    modules=modules, callback=cb, close_callback=self.drawer.close_panel)

    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        item_id = sel[0]

        is_module = False
        if self.is_advanced:
            if "module" in self.tree.item(item_id, "tags"): is_module = True

        if is_module:
            if item_id == "general":
                messagebox.showinfo(self.txt.get("title_info", "Info"),
                                    self.txt.get("msg_cannot_del_gen", "Cannot delete General container."))
                return
            if messagebox.askyesno(self.txt.get("btn_delete", "Delete"),
                                   self.txt.get("msg_confirm_del_mod", "Delete module and ALL its grades?")):
                self.storage.delete_grade_module(item_id)
                self.refresh_tree()
                self.refresh_subjects_list()
        else:
            if messagebox.askyesno(self.txt.get("btn_delete", "Delete"),
                                   self.txt.get("msg_confirm_del_grade", "Delete grade?")):
                self.storage.delete_grade(item_id)
                self.refresh_tree()
                self.refresh_subjects_list()

    def edit_item(self):
        sel = self.tree.selection()
        if not sel: return
        item_id = sel[0]

        if self.is_advanced and "module" in self.tree.item(item_id, "tags"):
            if item_id == "general": return
            messagebox.showinfo(self.txt.get("title_info", "Info"), self.txt.get("msg_mod_edit_impl",
                                                                                 "Module editing not implemented yet."))
            return

        all_grades = self.storage.get_grades(self.current_subject_id)
        target_grade = next((g for g in all_grades if g["id"] == item_id), None)

        if target_grade:
            modules = []
            if self.is_advanced:
                modules = [dict(m) for m in self.storage.get_grade_modules(self.current_subject_id)]

            cb = lambda: [self.refresh_tree(), self.refresh_subjects_list()]
            if self.drawer:
                self.drawer.set_content(AddGradePanel, txt=self.txt, btn_style=self.btn_style,
                                        storage=self.storage, subject_id=self.current_subject_id,
                                        grade_mode=self.grade_mode, weight_mode=self.weight_mode,
                                        modules=modules, grade_data=dict(target_grade),
                                        callback=cb, close_callback=self.drawer.close_panel)


# --- PANEL DODAWANIA MODUŁU (SZUFLADA) ---
class AddModulePanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, subject_id, callback=None, close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.storage = storage
        self.subject_id = subject_id
        self.callback = callback
        self.close_callback = close_callback
        self.btn_style = btn_style

        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(expand=True, fill="x", padx=30)
        self.center_box.grid_columnconfigure(0, weight=1)
        self.center_box.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(self.center_box, text=self.txt.get("win_add_module", "Add Module"),
                     font=("Arial", 20, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ctk.CTkLabel(self.center_box, text=self.txt.get("lbl_module_name", "Module Name")).grid(row=1, column=0,
                                                                                                sticky="e", padx=10)
        self.ent_name = ctk.CTkEntry(self.center_box)
        self.ent_name.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(self.center_box, text=self.txt.get("lbl_weight_perc", "Weight (%)")).grid(row=2, column=0,
                                                                                               sticky="e", padx=10)
        self.ent_weight = ctk.CTkEntry(self.center_box)
        self.ent_weight.grid(row=2, column=1, sticky="ew", padx=10, pady=10)

        btn_box = ctk.CTkFrame(self.center_box, fg_color="transparent")
        btn_box.grid(row=3, column=0, columnspan=2, pady=30)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **self.btn_style).pack(
            side="left", padx=10)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.perform_close,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      height=32, corner_radius=20, font=("Arial", 13, "bold"), border_color="gray",
                      hover_color=("gray80", "gray30")).pack(side="left", padx=10)

    def perform_close(self):
        if self.close_callback: self.close_callback()

    def save(self):
        try:
            w = float(self.ent_weight.get())
            name = self.ent_name.get()
            if name:
                self.storage.add_grade_module({
                    "id": f"mod_{uuid.uuid4().hex[:8]}",
                    "subject_id": self.subject_id,
                    "name": name,
                    "weight": w
                })
                if self.callback: self.callback()
                self.perform_close()
        except ValueError:
            messagebox.showerror(self.txt.get("title_error", "Error"),
                                 self.txt.get("msg_weight_error", "Weight must be a number"))


# --- PANEL DODAWANIA OCENY (SZUFLADA) ---
class AddGradePanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, subject_id, grade_mode, weight_mode,
                 modules=None, grade_data=None, callback=None, close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.subject_id = subject_id
        self.grade_mode = grade_mode
        self.weight_mode = weight_mode
        self.modules = modules or []
        self.grade_data = grade_data
        self.callback = callback
        self.close_callback = close_callback

        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(expand=True, fill="x", padx=30)
        self.center_box.grid_columnconfigure(0, weight=1)
        self.center_box.grid_columnconfigure(1, weight=2)

        title = self.txt.get("win_grade_add", "Add Grade") if not grade_data else self.txt.get("win_grade_edit",
                                                                                               "Edit Grade")
        ctk.CTkLabel(self.center_box, text=title, font=("Arial", 20, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                   pady=(0, 20))

        # OPIS
        ctk.CTkLabel(self.center_box, text=self.txt.get("col_desc", "Description")).grid(row=1, column=0, sticky="e",
                                                                                         padx=10, pady=5)

        exam_titles = []
        try:
            all_exams = [dict(e) for e in self.storage.get_exams()]
            exam_titles = [e["title"] for e in all_exams if e.get("subject_id") == self.subject_id]
        except Exception:
            pass

        base_values = ["Exam", "Test", "Quiz", "Homework", "Project", "Activity"]
        final_values = base_values + [t for t in exam_titles if t not in base_values]

        self.combo_desc = ctk.CTkComboBox(self.center_box, values=final_values)
        self.combo_desc.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        if grade_data: self.combo_desc.set(grade_data["desc"])

        # MODUŁ
        current_row = 2
        self.combo_mod = None
        if self.modules:
            ctk.CTkLabel(self.center_box, text=self.txt.get("lbl_module_parent", "Module")).grid(row=current_row,
                                                                                                 column=0, sticky="e",
                                                                                                 padx=10, pady=5)
            mod_names = [m["name"] for m in self.modules]
            self.combo_mod = ctk.CTkComboBox(self.center_box, values=mod_names)
            self.combo_mod.grid(row=current_row, column=1, sticky="ew", padx=10, pady=5)

            if grade_data and grade_data.get("module_id"):
                curr_mod = next((m for m in self.modules if m["id"] == grade_data["module_id"]), None)
                if curr_mod: self.combo_mod.set(curr_mod["name"])
            elif mod_names:
                self.combo_mod.set(mod_names[0])
            current_row += 1

        # PUNKTY
        ctk.CTkLabel(self.center_box, text="Points (Opt):").grid(row=current_row, column=0, sticky="e", padx=10, pady=5)

        pts_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        pts_frame.grid(row=current_row, column=1, sticky="w", padx=10, pady=5)

        self.ent_pts_got = ctk.CTkEntry(pts_frame, width=50, placeholder_text="0")
        self.ent_pts_got.pack(side="left", padx=5)
        ctk.CTkLabel(pts_frame, text="/", font=("Arial", 16, "bold")).pack(side="left")
        self.ent_pts_max = ctk.CTkEntry(pts_frame, width=50, placeholder_text="Max")
        self.ent_pts_max.pack(side="left", padx=5)

        self.ent_pts_got.bind("<KeyRelease>", self._calculate_points)
        self.ent_pts_max.bind("<KeyRelease>", self._calculate_points)
        current_row += 1

        # OCENA
        lbl_val_txt = self.txt.get("lbl_grade_perc", "Grade (%)") if grade_mode == 'percentage' else self.txt.get(
            "lbl_grade_val", "Grade")
        ctk.CTkLabel(self.center_box, text=lbl_val_txt).grid(row=current_row, column=0, sticky="e", padx=10, pady=5)
        self.ent_grade = ctk.CTkEntry(self.center_box)
        self.ent_grade.grid(row=current_row, column=1, sticky="ew", padx=10, pady=5)
        if grade_data: self.ent_grade.insert(0, str(grade_data["value"]))
        current_row += 1

        # WAGA
        lbl_weight_txt = self.txt.get("lbl_weight_perc", "Weight (%)") if weight_mode == 'percentage' else self.txt.get(
            "col_weight", "Weight")
        ctk.CTkLabel(self.center_box, text=lbl_weight_txt).grid(row=current_row, column=0, sticky="e", padx=10, pady=5)
        self.ent_weight = ctk.CTkEntry(self.center_box)
        self.ent_weight.grid(row=current_row, column=1, sticky="ew", padx=10, pady=5)
        if grade_data:
            self.ent_weight.insert(0, str(grade_data["weight"]))
        else:
            self.ent_weight.insert(0, "1")
        current_row += 1

        # DATA
        ctk.CTkLabel(self.center_box, text=self.txt.get("col_date", "Date")).grid(row=current_row, column=0, sticky="e",
                                                                                  padx=10, pady=5)

        date_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        date_frame.grid(row=current_row, column=1, sticky="w", padx=10, pady=5)
        self.cal_date = DateEntry(date_frame, width=15, date_pattern='y-mm-dd', background='#3a3a3a',
                                  foreground='white', borderwidth=0)
        self.cal_date.pack()
        if grade_data and grade_data.get("date"):
            try:
                self.cal_date.set_date(datetime.strptime(grade_data["date"], "%Y-%m-%d").date())
            except:
                pass
        current_row += 1

        # PRZYCISKI
        btn_box = ctk.CTkFrame(self.center_box, fg_color="transparent")
        btn_box.grid(row=current_row, column=0, columnspan=2, pady=30)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **self.btn_style).pack(
            side="left", padx=10)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.perform_close,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      height=32, corner_radius=20, font=("Arial", 13, "bold"), border_color="gray",
                      hover_color=("gray80", "gray30")).pack(side="left", padx=10)

    def perform_close(self):
        if self.close_callback: self.close_callback()

    def _calculate_points(self, event=None):
        got_str = self.ent_pts_got.get()
        max_str = self.ent_pts_max.get()
        if not got_str or not max_str: return
        try:
            got = float(got_str)
            max_val = float(max_str)
            if max_val > 0:
                perc = (got / max_val) * 100
                self.ent_grade.delete(0, "end")
                self.ent_grade.insert(0, f"{perc:.1f}")
        except ValueError:
            pass

    def save(self):
        desc = self.combo_desc.get().strip()
        date_str = str(self.cal_date.get_date())

        try:
            val = float(self.ent_grade.get())
            w = float(self.ent_weight.get())
        except ValueError:
            messagebox.showwarning(self.txt.get("title_error", "Error"),
                                   self.txt.get("msg_grade_num_error", "Grade and Weight must be numbers."))
            return

        if self.grade_mode == "percentage" and (val < 0 or val > 100):
            messagebox.showwarning(self.txt.get("title_error", "Error"),
                                   self.txt.get("msg_grade_perc_error", "Grade % must be 0-100."))
            return

        module_id = None
        if self.modules and self.combo_mod:
            name = self.combo_mod.get()
            found = next((m for m in self.modules if m["name"] == name), None)
            if found: module_id = found["id"]

        data = {
            "id": self.grade_data["id"] if self.grade_data else f"grade_{uuid.uuid4().hex[:8]}",
            "subject_id": self.subject_id,
            "module_id": module_id,
            "value": val, "weight": w, "desc": desc, "date": date_str
        }

        if self.grade_data:
            self.storage.delete_grade(data["id"])
            self.storage.add_grade(data)
        else:
            self.storage.add_grade(data)

        if self.callback: self.callback()
        self.perform_close()