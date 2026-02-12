import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date
from core.planner import date_format
from gui.dialogs.notebook import NotebookWindow


class ArchiveWindow:
    def __init__(self, parent, txt, btn_style, edit_exam_func, edit_topic_func, dashboard_callback=None, storage=None):
        self.txt = txt
        self.storage = storage
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback

        self.edit_exam_func = edit_exam_func
        self.edit_topic_func = edit_topic_func

        # Cache semestrów (nazwa -> id)
        self.semester_map = {}

        # USTAWIENIE OKNA
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt["win_archive_title"])
        self.win.geometry("800x600")

        # --- GÓRNY PASEK (FILTR SEMESTRÓW) ---
        top_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        top_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Etykieta
        ctk.CTkLabel(top_frame, text=self.txt.get("lbl_semester", "Semester") + ":",
                     font=("Arial", 12, "bold")).pack(side="left", padx=(5, 10))

        # ComboBox Semestrów
        self.combo_semester = ctk.CTkComboBox(top_frame, width=200, command=self.on_semester_change)
        self.combo_semester.pack(side="left")

        # Ładowanie semestrów
        self.load_semesters()

        # LABELE NAGŁÓWKOWE
        # 1. Główny tytuł
        ctk.CTkLabel(self.win, text=self.txt["msg_archive_header"], font=("Arial", 16, "bold")).pack(pady=(10, 0))

        # 2. PRZYWRÓCONY NAPIS "Double click to see details"
        sub_text = self.txt.get("msg_archive_sub", "Double click to see details")
        ctk.CTkLabel(self.win, text=sub_text, font=("Arial", 12)).pack(pady=(0, 10))

        # RAMKA TABELI
        frame = ctk.CTkFrame(self.win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        # TREE - LISTA Z DANYMI
        columns = ("data", "forma", "status", "postep")
        self.tree = ttk.Treeview(frame, columns=columns, show="tree headings", selectmode="browse")

        # Konfiguracja głównej kolumny (Drzewo - Przedmiot)
        self.tree.heading("#0", text=self.txt["col_subject"], anchor="w")
        self.tree.column("#0", width=250, anchor="w")

        # Konfiguracja pozostałych kolumn
        self.tree.heading("data", text=self.txt["col_date"])
        self.tree.column("data", width=100, anchor="center")

        self.tree.heading("forma", text=self.txt["col_form"])
        self.tree.column("forma", width=150, anchor="w")

        self.tree.heading("status", text=self.txt["col_status"])
        self.tree.column("status", width=120, anchor="center")

        col_prog_txt = self.txt.get("col_progress", "Progress")
        self.tree.heading("postep", text=col_prog_txt)
        self.tree.column("postep", width=100, anchor="center")

        # Tagi stylów - CZCIONKA 12 BOLD
        current_mode = ctk.get_appearance_mode()
        active_color = "#0066cc" if current_mode == "Light" else "lightblue"

        # Styl nagłówka przedmiotu
        bg_subject = "#e1e1e1" if current_mode == "Light" else "#333333"
        self.tree.tag_configure("subject_row", font=("Arial", 12, "bold"), background=bg_subject)

        # Styl egzaminów (dzieci)
        self.tree.tag_configure("active", foreground=active_color, font=("Arial", 12, "bold"))
        self.tree.tag_configure("past", foreground="gray", font=("Arial", 12, "bold"))

        # Scrollbar
        scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=self.tree.yview, fg_color="transparent",
                                     bg_color="transparent")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.tree.pack(side="left", fill="both", expand=True)

        # Bindings
        self.tree.bind("<Double-1>", self.on_double_click)

        # PRZYCISKI
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=10)

        btn_del_sel = ctk.CTkButton(btn_frame, text=self.txt["btn_del_selected"], command=self.delete_selected,
                                    **self.btn_style)
        btn_del_sel.pack(side="left", padx=5)

        btn_close = ctk.CTkButton(btn_frame, text=self.txt["btn_close"], command=self.win.destroy, **self.btn_style)
        btn_close.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        btn_close.pack(side="left", padx=5)

        self.refresh_list()

    def load_semesters(self):
        if not self.storage: return

        semesters = self.storage.get_semesters()
        semesters.sort(key=lambda x: (not x["is_current"], x["start_date"]), reverse=True)

        values = [self.txt.get("val_all", "All")]
        self.semester_map = {self.txt.get("val_all", "All"): None}

        for sem in semesters:
            name = sem["name"]
            if sem["is_current"]:
                name += f" ({self.txt.get('tag_current', 'Current')})"
            values.append(name)
            self.semester_map[name] = sem["id"]

        self.combo_semester.configure(values=values)
        self.combo_semester.set(values[0])

    def on_semester_change(self, choice):
        self.refresh_list()

    def refresh_list(self):
        if not self.storage:
            return

        # Czyścimy drzewo
        for item in self.tree.get_children():
            self.tree.delete(item)

        today = date.today()

        # Filtrowanie semestrów
        selected_sem_name = self.combo_semester.get()
        selected_sem_id = self.semester_map.get(selected_sem_name)

        all_subjects = [dict(s) for s in self.storage.get_subjects()]

        if selected_sem_id:
            subjects_to_show = [s for s in all_subjects if s["semester_id"] == selected_sem_id]
        else:
            subjects_to_show = all_subjects

        subjects_to_show.sort(key=lambda x: x["name"])
        all_exams = [dict(e) for e in self.storage.get_exams()]

        for subject in subjects_to_show:
            sub_exams = [e for e in all_exams if e["subject_id"] == subject["id"]]
            sub_exams.sort(key=lambda x: str(x["date"] or "9999-99-99"))

            # Logika domyślnego otwierania:
            is_expanded = False
            for e in sub_exams:
                if date_format(e["date"]) >= today:
                    is_expanded = True
                    break

            # Statystyki
            total_topics = 0
            done_topics = 0

            # Węzeł RODZICA (Przedmiot)
            parent_id = self.tree.insert("", "end", text=subject["name"], open=is_expanded, tags=("subject_row",))

            for exam in sub_exams:
                exam_date = date_format(exam["date"])
                days = (exam_date - today).days

                status_txt = ""
                tag = "active"

                if days < 0:
                    status_txt = self.txt["tag_archived"]
                    tag = "past"
                elif days == 0:
                    status_txt = self.txt["tag_today"]
                else:
                    status_txt = self.txt["tag_x_days"].format(days=days)

                topics_rows = self.storage.get_topics(exam["id"])
                t_total = len(topics_rows)
                t_done = len([t for t in topics_rows if t["status"] == "done"])

                total_topics += t_total
                done_topics += t_done

                progress_str = f"{t_done} / {t_total}"

                # Węzeł DZIECKA (Egzamin)
                self.tree.insert(parent_id, "end", iid=exam["id"],
                                 values=(exam["date"], exam["title"], status_txt, progress_str),
                                 tags=(tag,))

            if total_topics > 0:
                pct = int((done_topics / total_topics) * 100)
                summary = f"{done_topics}/{total_topics} ({pct}%)"
                self.tree.set(parent_id, "postep", summary)

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_del"])
            return

        item_id = selection[0]

        if not str(item_id).startswith("exam_"):
            messagebox.showwarning(self.txt["msg_warning"],
                                   self.txt.get("msg_select_exam_node", "Select an exam, not a subject."))
            return

        target_exam = self.storage.get_exam(item_id)
        if target_exam:
            name = target_exam["subject"]
            type_of_exam = target_exam["title"]

            confirm = messagebox.askyesno(self.txt["msg_warning"],
                                          self.txt["msg_confirm_del_perm"].format(type=type_of_exam, name=name))
            if confirm:
                if self.storage:
                    self.storage.delete_exam(item_id)
                self.refresh_list()
                messagebox.showinfo(self.txt["msg_success"], self.txt["msg_archived_del"])

    def on_double_click(self, event):
        """Obsługa podwójnego kliknięcia z blokadą propagacji dla nagłówków."""
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]

        # Sprawdzenie czy to egzamin (ID zaczyna się od "exam_")
        if str(item_id).startswith("exam_"):
            # To jest egzamin -> Otwórz szczegóły
            selected_exam_row = self.storage.get_exam(item_id)
            if selected_exam_row:
                self.open_details_window(dict(selected_exam_row))
        else:
            # To jest Przedmiot (nagłówek)
            # Ręcznie przełączamy stan, aby mieć pewność działania
            if self.tree.item(item_id, "open"):
                self.tree.item(item_id, open=False)
            else:
                self.tree.item(item_id, open=True)

            # Zwracamy "break", aby zatrzymać domyślne zdarzenie Treeview
            # (zapobiega to sytuacji, gdzie skrypt otwiera, a Treeview natychmiast zamyka)
            return "break"

    # --- OKNO SZCZEGÓŁÓW (Bez zmian logicznych) ---
    def open_details_window(self, exam_data):
        hist_window = tk.Toplevel(self.win)
        hist_window.minsize(600, 450)

        info_frame = ctk.CTkFrame(hist_window, fg_color="transparent")
        info_frame.pack(pady=10)

        lbl_subject = ctk.CTkLabel(info_frame, text="", font=("Arial", 12, "bold"))
        lbl_subject.pack()
        lbl_date = ctk.CTkLabel(info_frame, text="", font=("Arial", 12, "bold"))
        lbl_date.pack()

        def refresh_info():
            lbl_subject.configure(text=f"{exam_data['subject']} ({exam_data['title']})")
            lbl_date.configure(text=self.txt["msg_exam_date"].format(date=exam_data['date']))
            hist_window.title(self.txt["win_archive_details_title"].format(subject=exam_data['subject']))

        refresh_info()

        action_frame = ctk.CTkFrame(hist_window, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(0, 5))

        btn_notebook = ctk.CTkButton(action_frame,
                                     text=self.txt.get('btn_notebook', 'Notatnik'),
                                     height=28, width=100,
                                     fg_color="transparent", border_width=1, border_color="gray",
                                     text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                                     command=lambda: NotebookWindow(hist_window, self.txt,
                                                                    self.btn_style, exam_data,
                                                                    storage=self.storage))
        btn_notebook.pack(side="left")

        lbl_progress = ctk.CTkLabel(action_frame, text="", font=("Arial", 13, "bold"))
        lbl_progress.pack(side="right")

        frame = tk.Frame(hist_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("temat", "status", "data_plan")
        tree = ttk.Treeview(frame, columns=columns, show="headings")

        tree.heading("temat", text=self.txt["col_topic"])
        tree.column("temat", width=250, anchor="w")
        tree.heading("status", text=self.txt["col_status"])
        tree.column("status", width=100, anchor="center")
        tree.heading("data_plan", text=self.txt["col_plan_date"])
        tree.column("data_plan", width=120, anchor="center")

        tree.tag_configure("done", foreground="green", font=("Arial", 12, "bold"))
        tree.tag_configure("todo", foreground="red", font=("Arial", 13, "bold"))

        scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=tree.yview, fg_color="transparent",
                                     bg_color="transparent")
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        tree.pack(side="left", fill="both", expand=True)

        def refresh_details():
            for item in tree.get_children():
                tree.delete(item)

            topics_rows = self.storage.get_topics(exam_data["id"])
            exam_topics = [dict(t) for t in topics_rows]
            exam_topics.sort(key=lambda x: str(x.get("scheduled_date") or "9999-99-99"))

            total = len(exam_topics)
            done = len([t for t in exam_topics if t["status"] == "done"])
            pct = int((done / total) * 100) if total > 0 else 0

            prog_txt = self.txt.get("col_progress", "Progress")
            lbl_progress.configure(text=f"{prog_txt}: {done}/{total} ({pct}%)")

            for topic in exam_topics:
                status_text = self.txt["tag_done"] if topic["status"] == "done" else self.txt["tag_todo"]
                sched_date = topic.get("scheduled_date") if topic.get("scheduled_date") else "-"
                tree.insert("", "end", iid=topic["id"], values=(topic["name"], status_text, sched_date),
                            tags=(topic["status"],))

        refresh_details()

        def toggle_status_local():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_topic"])
                return
            topic_id = selected[0]
            topic_row = self.storage.get_topic(topic_id)
            if topic_row:
                topic = dict(topic_row)
                topic["status"] = "done" if topic["status"] == "todo" else "todo"
                self.storage.update_topic(topic)
                if topic["status"] == "done":
                    stats = self.storage.get_global_stats()
                    done_count = stats.get("topics_done", 0) + 1
                    self.storage.update_global_stat("topics_done", done_count)
                    self.storage.update_global_stat("activity_started", True)
                refresh_details()
                self.refresh_list()
                if self.dashboard_callback:
                    self.dashboard_callback()

        def edit_topic_local():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_topic"])
                return
            topic_id = selected[0]
            topic_row = self.storage.get_topic(topic_id)
            if topic_row:
                self.edit_topic_func(dict(topic_row), callback=refresh_details)

        def edit_exam_local():
            def saved():
                refresh_details()
                refresh_info()
                self.refresh_list()

            self.edit_exam_func(exam_data, callback=saved)

        tree.bind("<Double-1>", lambda event: edit_topic_local())

        ctk.CTkLabel(hist_window, text=self.txt["msg_double_click_edit"], font=("Arial", 12, "bold")).pack()
        btn_frame = ctk.CTkFrame(hist_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        btn_status = ctk.CTkButton(btn_frame, text=self.txt["btn_toggle_status"], command=toggle_status_local,
                                   **self.btn_style)
        btn_status.pack(side="left", padx=5)
        btn_edit = ctk.CTkButton(btn_frame, text=self.txt["btn_edit_exam"], command=edit_exam_local, **self.btn_style)
        btn_edit.pack(side="left", padx=5)
        btn_close = ctk.CTkButton(btn_frame, text=self.txt["btn_close"], command=hist_window.destroy, **self.btn_style)
        btn_close.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        btn_close.pack(side="left", padx=5)