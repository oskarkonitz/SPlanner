import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, date
import uuid


class GradesWindow:
    def __init__(self, parent, txt, btn_style, storage):
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage

        self.current_semester_id = None
        self.semesters = []
        self.subjects_data = []  # Lista przedmiotów w semestrze
        self.current_subject_id = None

        # Pobieranie ustawień z bazy
        settings = self.storage.get_settings().get("grading_system", {})
        self.grade_mode = settings.get("grade_mode", "percentage")  # percentage / numeric
        self.weight_mode = settings.get("weight_mode", "percentage")  # percentage / numeric

        # GŁÓWNE OKNO
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_grades_title", "Grades Manager"))
        self.win.geometry("950x600")
        self.win.minsize(800, 500)

        # UKŁAD GŁÓWNY (GRID)
        self.win.columnconfigure(0, weight=3)  # Lewy (Lista przedmiotów)
        self.win.columnconfigure(1, weight=7)  # Prawy (Tabela ocen)
        self.win.rowconfigure(0, weight=1)

        # --- LEWY PANEL: PRZEDMIOTY ---
        self.frame_left = ctk.CTkFrame(self.win, corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        self._init_left_panel()

        # --- PRAWY PANEL: OCENY ---
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

        # Ładowanie danych
        self.load_data()

    def _init_left_panel(self):
        # Nagłówek z wyborem semestru
        self.top_left = ctk.CTkFrame(self.frame_left, fg_color="transparent")
        self.top_left.pack(fill="x", pady=10, padx=10)

        ctk.CTkLabel(self.top_left, text=self.txt.get("lbl_semester", "Semester"), font=("Arial", 12, "bold")).pack(
            anchor="w")
        self.combo_sem = ctk.CTkComboBox(self.top_left, command=self.on_semester_change)
        self.combo_sem.pack(fill="x", pady=(5, 5))

        # --- NOWE: ŚREDNIA SEMESTRU ---
        self.lbl_sem_gpa = ctk.CTkLabel(self.top_left, text="GPA: --", font=("Arial", 14, "bold"), text_color="#2ecc71")
        self.lbl_sem_gpa.pack(anchor="w", pady=(0, 10))

        # Lista przedmiotów (Scrollable)
        self.scroll_subjects = ctk.CTkScrollableFrame(self.frame_left, fg_color="transparent")
        self.scroll_subjects.pack(fill="both", expand=True, padx=5, pady=5)

    def _init_right_panel(self):
        # 1. EMPTY STATE
        self.frame_empty = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        ctk.CTkLabel(self.frame_empty, text="⬅", font=("Arial", 40)).pack(pady=(150, 10))
        ctk.CTkLabel(self.frame_empty, text=self.txt.get("msg_select_subj_grades", "Select a subject to view grades."),
                     font=("Arial", 14), text_color="gray").pack()

        # 2. CONTENT STATE
        self.frame_content = ctk.CTkFrame(self.frame_right, fg_color="transparent")

        # Nagłówek Przedmiotu
        header_frame = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=10)

        self.lbl_subj_title = ctk.CTkLabel(header_frame, text="Subject Name", font=("Arial", 20, "bold"))
        self.lbl_subj_title.pack(side="left")

        self.lbl_subj_avg = ctk.CTkLabel(header_frame, text="Avg: --", font=("Arial", 16, "bold"), text_color="#3498db")
        self.lbl_subj_avg.pack(side="left", padx=20)

        ctk.CTkButton(header_frame, text="+ " + self.txt.get("btn_add_grade", "Add Grade"),
                      command=self.add_grade, **self.btn_style).pack(side="right")

        # Tabela Ocen (Treeview)
        style = ttk.Style()
        style.configure("Grades.Treeview", rowheight=35, font=("Arial", 13))
        style.configure("Grades.Treeview.Heading", font=("Arial", 13, "bold"))

        cols = ("date", "desc", "weight", "grade")
        self.tree_grades = ttk.Treeview(self.frame_content, columns=cols, show="headings", selectmode="browse",
                                        style="Grades.Treeview")

        self.tree_grades.heading("date", text=self.txt.get("col_date", "Date"))
        self.tree_grades.column("date", width=100, anchor="center")

        self.tree_grades.heading("desc", text=self.txt.get("col_desc", "Description"))
        self.tree_grades.column("desc", width=250, anchor="w")

        self.tree_grades.heading("weight", text=self.txt.get("col_weight_val", "Weight"))
        self.tree_grades.column("weight", width=80, anchor="center")

        self.tree_grades.heading("grade", text=self.txt.get("col_grade", "Grade"))
        self.tree_grades.column("grade", width=80, anchor="center")

        self.tree_grades.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Przyciski Edycji
        btn_box = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        btn_box.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_edit", "Edit"), command=self.edit_grade,
                      **self.btn_style).pack(side="left", padx=5)

        del_style = self.btn_style.copy()
        del_style["fg_color"] = "#e74c3c"
        del_style["hover_color"] = "#c0392b"
        ctk.CTkButton(btn_box, text=self.txt.get("btn_delete", "Delete"), command=self.delete_grade,
                      **del_style).pack(side="right", padx=5)

        self.show_right_panel(empty=True)

    def show_right_panel(self, empty=True):
        if empty:
            self.frame_content.pack_forget()
            self.frame_empty.pack(fill="both", expand=True)
        else:
            self.frame_empty.pack_forget()
            self.frame_content.pack(fill="both", expand=True)

    # --- LOGIKA DANYCH ---

    def load_data(self):
        # Ładujemy semestry
        self.semesters = [dict(s) for s in self.storage.get_semesters()]
        self.semesters.sort(key=lambda x: not x["is_current"])

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
        # Czyścimy listę
        for widget in self.scroll_subjects.winfo_children():
            widget.destroy()

        if not self.current_semester_id: return

        # Pobieramy przedmioty
        self.subjects_data = [dict(s) for s in self.storage.get_subjects(self.current_semester_id)]

        for sub in self.subjects_data:
            # Obliczamy średnią i formatujemy tekst
            avg_val = self._get_raw_subject_avg(sub["id"])
            if avg_val is None:
                avg_str = "Avg: --"
            else:
                if self.grade_mode == "percentage":
                    avg_str = f"Avg: {int(avg_val)}%"
                else:
                    avg_str = f"Avg: {avg_val:.2f}"

            # Bezpieczny kolor
            safe_color = sub["color"] if sub.get("color") else "#3498db"

            # Kafelki Outline
            btn_text = f"{sub['name']}\n{avg_str}"
            btn = ctk.CTkButton(self.scroll_subjects, text=btn_text, height=55,
                                fg_color="transparent",
                                border_color=safe_color,
                                border_width=2,
                                text_color=("gray10", "gray90"),
                                hover_color=("gray85", "gray25"),
                                font=("Arial", 12, "bold"),
                                command=lambda s=sub: self.open_subject_details(s))
            btn.pack(fill="x", pady=4)

        # PRZELICZ ŚREDNIĄ SEMESTRU (ECTS)
        self._update_semester_gpa()

    def _get_raw_subject_avg(self, subject_id):
        """Zwraca surową wartość liczbową średniej przedmiotu lub None."""
        grades = [dict(g) for g in self.storage.get_grades(subject_id)]
        if not grades: return None

        total_weight = 0
        weighted_sum = 0

        for g in grades:
            w = g["weight"]
            v = g["value"]
            weighted_sum += v * w
            total_weight += w

        if total_weight == 0: return None
        return weighted_sum / total_weight

    def _calculate_subject_avg(self, subject_id):
        """Wrapper formatujący tekstowo do nagłówka."""
        val = self._get_raw_subject_avg(subject_id)
        if val is None: return "Avg: --"

        if self.grade_mode == "percentage":
            return f"Avg: {int(val)}%"
        else:
            return f"Avg: {val:.2f}"

    def _update_semester_gpa(self):
        """Oblicza średnią ważoną punktami ECTS (weight z tabeli subjects)."""
        if not self.subjects_data:
            self.lbl_sem_gpa.configure(text="GPA: --")
            return

        total_ects_points = 0
        weighted_grade_sum = 0

        # Iterujemy przez przedmioty wczytane do listy
        for sub in self.subjects_data:
            avg = self._get_raw_subject_avg(sub["id"])
            if avg is None:
                continue  # Pomiń przedmioty bez ocen (nie zaniżają średniej zerem)

            ects = sub.get("weight", 0)  # W SubjectManager "weight" to ECTS

            weighted_grade_sum += avg * ects
            total_ects_points += ects

        if total_ects_points == 0:
            self.lbl_sem_gpa.configure(text="GPA: --")
        else:
            final_gpa = weighted_grade_sum / total_ects_points

            if self.grade_mode == "percentage":
                txt = f"GPA: {int(final_gpa)}%"
            else:
                txt = f"GPA: {final_gpa:.2f}"

            self.lbl_sem_gpa.configure(text=txt)

    def open_subject_details(self, subject):
        self.current_subject_id = subject["id"]
        safe_color = subject["color"] if subject.get("color") else "gray"
        self.lbl_subj_title.configure(text=subject["name"], text_color=safe_color)
        self.show_right_panel(empty=False)
        self.refresh_grades_table()

    def refresh_grades_table(self):
        if not self.current_subject_id: return

        for item in self.tree_grades.get_children():
            self.tree_grades.delete(item)

        grades = [dict(g) for g in self.storage.get_grades(self.current_subject_id)]
        grades.sort(key=lambda x: x["date"], reverse=True)

        for g in grades:
            val_str = f"{int(g['value'])}%" if self.grade_mode == "percentage" else f"{g['value']:.1f}"
            weight_str = f"{int(g['weight'])}%" if self.weight_mode == "percentage" else f"{g['weight']:.1f}"

            self.tree_grades.insert("", "end", iid=g["id"], values=(g["date"], g["desc"], weight_str, val_str))

        self.lbl_subj_avg.configure(text=self._calculate_subject_avg(self.current_subject_id))

    # --- CRUD OCENY ---

    def add_grade(self):
        if not self.current_subject_id: return
        AddGradeWindow(self.win, self.txt, self.btn_style, self.storage,
                       self.current_subject_id, self.grade_mode, self.weight_mode,
                       callback=lambda: [self.refresh_grades_table(), self.refresh_subjects_list()])

    def edit_grade(self):
        sel = self.tree_grades.selection()
        if not sel: return

        grade_id = sel[0]
        grades = [dict(g) for g in self.storage.get_grades(self.current_subject_id)]
        grade_data = next((g for g in grades if g["id"] == grade_id), None)

        if grade_data:
            AddGradeWindow(self.win, self.txt, self.btn_style, self.storage,
                           self.current_subject_id, self.grade_mode, self.weight_mode,
                           grade_data=grade_data,
                           callback=lambda: [self.refresh_grades_table(), self.refresh_subjects_list()])

    def delete_grade(self):
        sel = self.tree_grades.selection()
        if not sel: return

        if messagebox.askyesno(self.txt["msg_warning"], self.txt.get("msg_confirm_del_grade", "Delete grade?")):
            self.storage.delete_grade(sel[0])
            self.refresh_grades_table()
            self.refresh_subjects_list()


class AddGradeWindow:
    def __init__(self, parent, txt, btn_style, storage, subject_id, grade_mode, weight_mode, grade_data=None,
                 callback=None):
        self.win = ctk.CTkToplevel(parent)
        self.txt = txt
        self.storage = storage
        self.subject_id = subject_id
        self.grade_mode = grade_mode
        self.weight_mode = weight_mode
        self.grade_data = grade_data
        self.callback = callback

        mode_str = "Edit" if grade_data else "Add"
        self.win.title(f"{mode_str} Grade")
        self.win.geometry("400x450")

        # 1. OPIS (COMBOBOX z nazwami egzaminów)
        ctk.CTkLabel(self.win, text=self.txt.get("form_desc", "Description")).pack(pady=(10, 2))

        exams = [dict(e) for e in self.storage.get_exams()]
        subj_exams = [e["title"] for e in exams if e.get("subject_id") == subject_id]

        self.combo_desc = ctk.CTkComboBox(self.win, width=250, values=subj_exams)
        self.combo_desc.pack(pady=5)
        self.combo_desc.set(grade_data["desc"] if grade_data else "")

        # 2. DATA
        ctk.CTkLabel(self.win, text=self.txt.get("form_date", "Date")).pack(pady=(10, 2))
        self.cal_date = DateEntry(self.win, width=12, date_pattern='y-mm-dd')
        self.cal_date.pack(pady=5)
        if grade_data: self.cal_date.set_date(grade_data["date"])

        # 3. WARTOŚĆ OCENY i WAGA (Obok siebie)
        f_vals = ctk.CTkFrame(self.win, fg_color="transparent")
        f_vals.pack(pady=15)

        # Grade
        f_g = ctk.CTkFrame(f_vals, fg_color="transparent")
        f_g.pack(side="left", padx=10)
        lbl_g = "Grade (%)" if grade_mode == "percentage" else "Grade (Val)"
        ctk.CTkLabel(f_g, text=lbl_g).pack()
        self.ent_grade = ctk.CTkEntry(f_g, width=80)
        self.ent_grade.pack()
        if grade_data: self.ent_grade.insert(0,
                                             str(int(grade_data["value"]) if grade_mode == "percentage" else grade_data[
                                                 "value"]))

        # Weight
        f_w = ctk.CTkFrame(f_vals, fg_color="transparent")
        f_w.pack(side="left", padx=10)
        lbl_w = "Weight (%)" if weight_mode == "percentage" else "Weight (Val)"
        ctk.CTkLabel(f_w, text=lbl_w).pack()
        self.ent_weight = ctk.CTkEntry(f_w, width=80)
        self.ent_weight.pack()
        val_w = grade_data["weight"] if grade_data else (100.0 if weight_mode == "percentage" else 1.0)
        self.ent_weight.insert(0, str(int(val_w) if weight_mode == "percentage" else val_w))

        # Przyciski
        btn_box = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_box.pack(pady=30, fill="x")

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **btn_style).pack(side="left",
                                                                                                           padx=20,
                                                                                                           expand=True)
        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=20,
                                                                                                    expand=True)

    def save(self):
        desc = self.combo_desc.get().strip()
        date_str = str(self.cal_date.get_date())

        try:
            val = float(self.ent_grade.get())
            w = float(self.ent_weight.get())
        except ValueError:
            messagebox.showwarning("Error", "Grade and Weight must be numbers.")
            return

        if self.grade_mode == "percentage" and (val < 0 or val > 100):
            messagebox.showwarning("Error", "Grade % must be 0-100.")
            return

        data = {
            "id": self.grade_data["id"] if self.grade_data else f"grade_{uuid.uuid4().hex[:8]}",
            "subject_id": self.subject_id,
            "value": val,
            "weight": w,
            "desc": desc,
            "date": date_str
        }

        if self.grade_data:
            self.storage.delete_grade(data["id"])
            self.storage.add_grade(data)
        else:
            self.storage.add_grade(data)

        if self.callback: self.callback()
        self.win.destroy()