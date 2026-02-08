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

        # DOMYŚLNIE FALSE - czyli stary tryb płaskiej listy
        self.is_advanced = settings.get("advanced_mode", False)

        # Domyślne progi, jeśli nie ustawiono w settings
        defaults_thresholds = {"3.0": 50, "3.5": 60, "4.0": 70, "4.5": 80, "5.0": 90}
        self.thresholds = settings.get("thresholds", defaults_thresholds)

        # GŁÓWNE OKNO
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_grades_title", "Grades Manager"))
        self.win.geometry("1000x700")
        self.win.minsize(900, 600)

        # UKŁAD GŁÓWNY (GRID)
        self.win.columnconfigure(0, weight=3)  # Lewy (Lista przedmiotów)
        self.win.columnconfigure(1, weight=7)  # Prawy (Tabela ocen)
        self.win.rowconfigure(0, weight=1)

        # --- LEWY PANEL: PRZEDMIOTY ---
        self.frame_left = ctk.CTkFrame(self.win, corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        self._init_left_panel()

        # --- PRAWY PANEL: SZCZEGÓŁY OCEN ---
        self.frame_right = ctk.CTkFrame(self.win, corner_radius=0, fg_color="transparent")
        self.frame_right.grid(row=0, column=1, sticky="nsew")
        self._init_right_panel()

        # STOPKA
        self.frame_footer = ctk.CTkFrame(self.win, height=40, corner_radius=0)
        self.frame_footer.grid(row=1, column=0, columnspan=2, sticky="ew")
        ctk.CTkButton(self.frame_footer, text=self.txt.get("btn_close", "Close"), command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=20, pady=10)

        self.load_data()

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

        # Przyciski akcji (Góra) - Moduł widoczny tylko w trybie Advanced
        if self.is_advanced:
            ctk.CTkButton(header_frame, text=self.txt.get("btn_add_module", "+ Module"), width=80, fg_color="#e67e22",
                          hover_color="#d35400",
                          command=self.add_module).pack(side="right", padx=5)

        ctk.CTkButton(header_frame, text=self.txt.get("btn_add_grade", "+ Grade"), width=80, command=self.add_grade,
                      **self.btn_style).pack(side="right", padx=5)

        # --- KONFIGURACJA STYLU DRZEWA (WIĘKSZA CZCIONKA) ---
        style = ttk.Style()
        # Ustawiamy globalnie większą czcionkę dla Treeview w tym oknie
        style.configure("Grades.Treeview", font=("Arial", 13), rowheight=30)
        style.configure("Grades.Treeview.Heading", font=("Arial", 13, "bold"), rowheight=30)

        # Tabela (Treeview)
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

        # Style tagów - POPRAWIONE KOLORY
        # Module: Pogrubiony, bez tła (żeby pasowało do Dark/Light), kolor tekstu neutralny/lekko inny
        # Grade: Zwykły tekst
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
        # Sortowanie semestrów: aktualny pierwszy, potem po dacie
        self.semesters.sort(key=lambda x: (not x["is_current"], x["start_date"]), reverse=True)

        sem_names = [s["name"] for s in self.semesters]
        self.combo_sem.configure(values=sem_names)

        if self.semesters:
            if not self.current_semester_id:
                # Domyślnie wybierz pierwszy (najbardziej aktualny)
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
        # Czyścimy listę po lewej
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
                # Pokazujemy też ocenę wynikającą z progów
                grade = self._percent_to_grade(final_percent)
                avg_str += f" ({grade})"

            # --- FIX: Pobranie koloru z zabezpieczeniem przed None ---
            color = sub.get("color")
            if not color:
                color = "gray"

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

        # --- FIX: Zabezpieczenie przed None w tytule ---
        color = subject.get("color")
        if not color:
            color = "gray"

        self.lbl_subj_title.configure(text=subject["name"], text_color=color)
        self.show_right_panel(empty=False)
        self.refresh_tree()

    def refresh_tree(self):
        # Czyścimy tabelę
        for i in self.tree.get_children():
            self.tree.delete(i)

        if not self.current_subject_id:
            return

        raw_grades = [dict(g) for g in self.storage.get_grades(self.current_subject_id)]

        # LOGIKA WYŚWIETLANIA: ADVANCED VS SIMPLE
        if self.is_advanced:
            # TRYB ZAAWANSOWANY: Drzewo Modułów
            modules = [dict(m) for m in self.storage.get_grade_modules(self.current_subject_id)]

            # Grupowanie ocen po modułach
            grouped = {m["id"]: [] for m in modules}
            ungrouped = []

            for g in raw_grades:
                mid = g.get("module_id")
                if mid and mid in grouped:
                    grouped[mid].append(g)
                else:
                    ungrouped.append(g)

            # Rysowanie modułów (Rodzice)
            for mod in modules:
                mod_avg = self._calculate_module_avg(grouped[mod["id"]])
                avg_val_txt = f"{mod_avg:.1f}%" if mod_avg is not None else "--"
                avg_label = self.txt.get("lbl_avg_short", "Avg")

                mid = self.tree.insert("", "end", iid=mod["id"], text=f"{mod['name']}",
                                       values=(f"{mod['weight']}%", f"{avg_label}: {avg_val_txt}", ""), open=True,
                                       tags=("module",))

                # Oceny w module (Dzieci)
                for g in grouped[mod["id"]]:
                    self._insert_grade_row(mid, g)

            # Rysowanie nieprzypisanych ocen
            if ungrouped:
                gen_name = self.txt.get("cat_general", "General / Uncategorized")
                gen_id = self.tree.insert("", "end", iid="general", text=gen_name,
                                          values=("??", "", ""), open=True, tags=("module",))
                for g in ungrouped:
                    self._insert_grade_row(gen_id, g)

        else:
            # TRYB DOMYŚLNY: Płaska lista (jak dawniej)
            for g in raw_grades:
                self._insert_grade_row("", g)

        # Aktualizacja nagłówka ze średnią
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

    # --- LOGIKA OBLICZEŃ ---

    def _calculate_module_avg(self, grades):
        """Oblicza średnią z listy ocen wewnątrz modułu."""
        if not grades: return None
        total_w = 0
        weighted_sum = 0

        for g in grades:
            val = g["value"]
            w = g["weight"]

            # Tutaj można dodać normalizację, jeśli oceny nie są procentowe
            weighted_sum += val * w
            total_w += w

        if total_w == 0: return 0
        return weighted_sum / total_w

    def _calculate_final_percentage(self, subject_id):
        """Oblicza końcowy wynik przedmiotu (0-100%)."""
        if self.is_advanced:
            # Algorytm Advanced: Suma średnich modułów ważona ich wagą
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
                    weight = mod["weight"]  # Waga modułu (np. 50%)
                    total_score += mod_avg * (weight / 100.0)
                    total_module_weight += weight

            if not has_any_grade and total_module_weight == 0:
                return None

            return total_score

        else:
            # Tryb Prosty: Zwykła średnia ważona wszystkich ocen
            grades = [dict(g) for g in self.storage.get_grades(subject_id)]
            return self._calculate_module_avg(grades)

    def _percent_to_grade(self, percent):
        """Mapuje % na ocenę (2.0 - 5.0) wg Settings."""
        if percent is None: return None
        # Sortujemy progi malejąco: 5.0 (90), 4.5 (80)...
        sorted_thresholds = sorted([(k, v) for k, v in self.thresholds.items()], key=lambda x: x[1], reverse=True)

        for grade, threshold in sorted_thresholds:
            if percent >= threshold:
                return float(grade)
        return 2.0

    def _update_semester_gpa(self):
        """Liczy GPA semestru używając wag przedmiotów (ECTS) i obliczonych ocen końcowych."""

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

            # Konwersja % -> Ocena (np. 4.5)
            grade_val = self._percent_to_grade(final_percent)
            ects = sub.get("weight", 0)  # W SubjectManager pole weight to ECTS

            weighted_sum += grade_val * ects
            total_ects += ects
            valid_subjects += 1

        if total_ects == 0 or valid_subjects == 0:
            self.lbl_sem_gpa.configure(text=gpa_txt)
        else:
            gpa = weighted_sum / total_ects
            lbl_gpa = self.txt.get("lbl_gpa", "GPA")
            self.lbl_sem_gpa.configure(text=f"{lbl_gpa}: {gpa:.2f}")

    # --- AKCJE CRUD (DODAWANIE/USUWANIE) ---

    def add_module(self):
        # To działa tylko w trybie Advanced
        if not self.current_subject_id: return
        dialog = ctk.CTkToplevel(self.win)
        dialog.title(self.txt.get("win_add_module", "Add Module"))
        dialog.geometry("300x200")
        dialog.transient(self.win)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=self.txt.get("lbl_module_name", "Module Name")).pack(pady=5)
        ent_name = ctk.CTkEntry(dialog)
        ent_name.pack(pady=5)

        ctk.CTkLabel(dialog, text=self.txt.get("lbl_weight_perc", "Weight (%)")).pack(pady=5)
        ent_weight = ctk.CTkEntry(dialog)
        ent_weight.pack(pady=5)

        def save():
            try:
                w = float(ent_weight.get())
                name = ent_name.get()
                if name:
                    self.storage.add_grade_module({
                        "id": f"mod_{uuid.uuid4().hex[:8]}",
                        "subject_id": self.current_subject_id,
                        "name": name,
                        "weight": w
                    })
                    self.refresh_tree()
                    self.refresh_subjects_list()  # Średnia mogła ulec zmianie
                    dialog.destroy()
            except ValueError:
                messagebox.showerror(self.txt.get("title_error", "Error"),
                                     self.txt.get("msg_weight_error", "Weight must be a number"))

        ctk.CTkButton(dialog, text=self.txt.get("btn_save", "Save"), command=save).pack(pady=10)

    def add_grade(self):
        if not self.current_subject_id:
            messagebox.showinfo(self.txt.get("title_info", "Info"),
                                self.txt.get("msg_select_subj", "Select a subject first."))
            return

        modules = []
        # Pobieramy moduły tylko jeśli tryb Advanced jest włączony
        if self.is_advanced:
            modules = [dict(m) for m in self.storage.get_grade_modules(self.current_subject_id)]

        AddGradeWindow(self.win, self.txt, self.btn_style, self.storage,
                       self.current_subject_id, self.grade_mode, self.weight_mode,
                       modules=modules,
                       callback=lambda: [self.refresh_tree(), self.refresh_subjects_list()])

    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        item_id = sel[0]

        # Sprawdzamy czy to moduł (tylko w trybie advanced)
        is_module = False
        if self.is_advanced:
            # Można sprawdzić po tagach w treeview
            if "module" in self.tree.item(item_id, "tags"):
                is_module = True

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
            # To ocena
            if messagebox.askyesno(self.txt.get("btn_delete", "Delete"),
                                   self.txt.get("msg_confirm_del_grade", "Delete grade?")):
                self.storage.delete_grade(item_id)
                self.refresh_tree()
                self.refresh_subjects_list()

    def edit_item(self):
        sel = self.tree.selection()
        if not sel: return
        item_id = sel[0]

        # Edycja modułu
        if self.is_advanced and "module" in self.tree.item(item_id, "tags"):
            if item_id == "general": return
            messagebox.showinfo(self.txt.get("title_info", "Info"), self.txt.get("msg_mod_edit_impl",
                                                                                 "Module editing not implemented yet. Delete and re-create."))
            return

        # Edycja oceny
        all_grades = self.storage.get_grades(self.current_subject_id)
        target_grade = next((g for g in all_grades if g["id"] == item_id), None)

        if target_grade:
            modules = []
            if self.is_advanced:
                modules = [dict(m) for m in self.storage.get_grade_modules(self.current_subject_id)]

            AddGradeWindow(self.win, self.txt, self.btn_style, self.storage,
                           self.current_subject_id, self.grade_mode, self.weight_mode,
                           modules=modules, grade_data=dict(target_grade),
                           callback=lambda: [self.refresh_tree(), self.refresh_subjects_list()])


class AddGradeWindow:
    def __init__(self, parent, txt, btn_style, storage, subject_id, grade_mode, weight_mode,
                 modules=None, grade_data=None, callback=None):
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.subject_id = subject_id
        self.grade_mode = grade_mode
        self.weight_mode = weight_mode
        self.modules = modules or []
        self.grade_data = grade_data
        self.callback = callback

        self.win = ctk.CTkToplevel(parent)
        title = self.txt.get("win_grade_add", "Add Grade") if not grade_data else self.txt.get("win_grade_edit",
                                                                                               "Edit Grade")
        self.win.title(title)
        self.win.geometry("450x550")  # Lekko powiększone dla nowych opcji
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()

        # --- FORMULARZ ---
        ctk.CTkLabel(self.win, text=self.txt.get("col_desc", "Description")).pack(pady=(10, 5))

        # --- ZMIANA: Pobieranie nazw egzaminów z bazy ---
        exam_titles = []
        try:
            # Pobieramy wszystkie egzaminy i filtrujemy dla obecnego przedmiotu
            all_exams = [dict(e) for e in self.storage.get_exams()]
            exam_titles = [e["title"] for e in all_exams if e.get("subject_id") == self.subject_id]
        except Exception:
            pass  # Ignorujemy błędy, jeśli baza jeszcze nie gotowa lub inna struktura

        base_values = ["Exam", "Test", "Quiz", "Homework", "Project", "Activity"]
        # Dodajemy unikalne nazwy egzaminów
        final_values = base_values + [t for t in exam_titles if t not in base_values]

        self.combo_desc = ctk.CTkComboBox(self.win, values=final_values)
        self.combo_desc.pack(pady=5)

        if grade_data: self.combo_desc.set(grade_data["desc"])

        # Wybór modułu (tylko jeśli przekazano moduły - czyli tryb Advanced)
        self.combo_mod = None
        if self.modules:
            ctk.CTkLabel(self.win, text=self.txt.get("lbl_module_parent", "Module (Parent)")).pack(pady=(10, 5))
            mod_names = [m["name"] for m in self.modules]
            self.combo_mod = ctk.CTkComboBox(self.win, values=mod_names)
            self.combo_mod.pack(pady=5)

            if grade_data and grade_data.get("module_id"):
                curr_mod = next((m for m in self.modules if m["id"] == grade_data["module_id"]), None)
                if curr_mod: self.combo_mod.set(curr_mod["name"])
            elif mod_names:
                self.combo_mod.set(mod_names[0])

        # --- NOWOŚĆ: PUNKTY OBLICZENIOWE (PO LEWEJ/NAD OCENĄ) ---
        ctk.CTkLabel(self.win, text=self.txt.get("lbl_points_opt", "Points (Optional - Auto Calc)")).pack(pady=(15, 5))

        pts_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        pts_frame.pack(pady=5)

        # Pole: Uzyskane
        self.ent_pts_got = ctk.CTkEntry(pts_frame, width=60, placeholder_text="0", justify="center")
        self.ent_pts_got.pack(side="left", padx=5)

        ctk.CTkLabel(pts_frame, text="/", font=("Arial", 16, "bold")).pack(side="left")

        # Pole: Maksymalne
        self.ent_pts_max = ctk.CTkEntry(pts_frame, width=60, placeholder_text="Max", justify="center")
        self.ent_pts_max.pack(side="left", padx=5)

        # Binding zdarzeń (automatyczne liczenie)
        self.ent_pts_got.bind("<KeyRelease>", self._calculate_points)
        self.ent_pts_max.bind("<KeyRelease>", self._calculate_points)

        # WARTOŚĆ (GRADE)
        lbl_val_txt = self.txt.get("lbl_grade_perc", "Grade (%)") if grade_mode == 'percentage' else self.txt.get(
            "lbl_grade_val", "Grade (Value)")
        ctk.CTkLabel(self.win, text=lbl_val_txt).pack(pady=(10, 5))

        self.ent_grade = ctk.CTkEntry(self.win)
        self.ent_grade.pack(pady=5)
        if grade_data: self.ent_grade.insert(0, str(grade_data["value"]))

        # WAGA
        lbl_weight_txt = self.txt.get("lbl_weight_perc", "Weight (%)") if weight_mode == 'percentage' else self.txt.get(
            "col_weight", "Weight")
        ctk.CTkLabel(self.win, text=lbl_weight_txt).pack(pady=(10, 5))

        self.ent_weight = ctk.CTkEntry(self.win)
        self.ent_weight.pack(pady=5)
        if grade_data:
            self.ent_weight.insert(0, str(grade_data["weight"]))
        else:
            self.ent_weight.insert(0, "1")

        # DATA
        ctk.CTkLabel(self.win, text=self.txt.get("col_date", "Date")).pack(pady=(10, 5))
        self.cal_date = DateEntry(self.win, width=20, date_pattern='y-mm-dd')
        self.cal_date.pack(pady=5)
        if grade_data and grade_data.get("date"):
            try:
                self.cal_date.set_date(datetime.strptime(grade_data["date"], "%Y-%m-%d").date())
            except:
                pass

        # BUTTONS
        btn_box = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_box.pack(pady=20, fill="x")

        ctk.CTkButton(btn_box, text=self.txt.get("btn_save", "Save"), command=self.save, **self.btn_style).pack(
            side="left", padx=20, expand=True)
        ctk.CTkButton(btn_box, text=self.txt.get("btn_cancel", "Cancel"), command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=20,
                                                                                                    expand=True)

    def _calculate_points(self, event=None):
        """Automatycznie przelicza punkty na procenty."""
        got_str = self.ent_pts_got.get()
        max_str = self.ent_pts_max.get()

        if not got_str or not max_str:
            return

        try:
            got = float(got_str)
            max_val = float(max_str)

            if max_val > 0:
                perc = (got / max_val) * 100

                # Aktualizacja pola oceny
                self.ent_grade.delete(0, "end")
                self.ent_grade.insert(0, f"{perc:.1f}")
        except ValueError:
            pass  # Ignorujemy niepełne dane

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

        # Ustalenie module_id
        module_id = None
        if self.modules and self.combo_mod:
            name = self.combo_mod.get()
            found = next((m for m in self.modules if m["name"] == name), None)
            if found: module_id = found["id"]

        data = {
            "id": self.grade_data["id"] if self.grade_data else f"grade_{uuid.uuid4().hex[:8]}",
            "subject_id": self.subject_id,
            "module_id": module_id,
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

        if self.callback:
            self.callback()
        self.win.destroy()