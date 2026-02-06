import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date
from core.planner import date_format
# from core.storage import save  <-- USUNIĘTO (zastąpione przez StorageManager)
from gui.windows.notebook import NotebookWindow  # <--- IMPORT NOWEGO OKNA


class ArchiveWindow:
    # ZAKTUALIZOWANA SYGNATURA: dodano argument storage=None
    def __init__(self, parent, txt, data, btn_style, edit_exam_func, edit_topic_func, dashboard_callback=None,
                 storage=None):
        self.txt = txt
        self.data = data  # Zachowane dla kompatybilności przekazywania do NotebookWindow
        self.storage = storage  # NOWE: StorageManager
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback

        self.edit_exam_func = edit_exam_func
        self.edit_topic_func = edit_topic_func

        # USTAWIENIE OKNA
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt["win_archive_title"])
        self.win.geometry("750x500")

        # LABELE
        ctk.CTkLabel(self.win, text=self.txt["msg_archive_header"], font=("Arial", 16, "bold")).pack(pady=10)
        ctk.CTkLabel(self.win, text=self.txt["msg_archive_sub"], font=("Arial", 12, "bold")).pack(pady=5)

        # RAMKA
        frame = ctk.CTkFrame(self.win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # TREE - LISTA Z DANYMI
        columns = ("data", "przedmiot", "forma", "status", "postep")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("data", text=self.txt["col_date"])
        self.tree.column("data", width=100, anchor="center")

        self.tree.heading("przedmiot", text=self.txt["col_subject"])
        self.tree.column("przedmiot", width=180, anchor="w")

        self.tree.heading("forma", text=self.txt["col_form"])
        self.tree.column("forma", width=120, anchor="w")

        self.tree.heading("status", text=self.txt["col_status"])
        self.tree.column("status", width=150, anchor="center")

        col_prog_txt = self.txt.get("col_progress", "Postęp")
        self.tree.heading("postep", text=col_prog_txt)
        self.tree.column("postep", width=80, anchor="center")

        current_mode = ctk.get_appearance_mode()
        active_color = "#0066cc" if current_mode == "Light" else "lightblue"

        self.tree.tag_configure("active", foreground=active_color, font=("Arial", 12, "bold"))
        self.tree.tag_configure("past", foreground="gray", font=("Arial", 12, "bold"))

        # scroll
        scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=self.tree.yview, fg_color="transparent",
                                     bg_color="transparent")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.tree.pack(side="left", fill="both", expand=True)

        # podwojne klikniecie otwiera szczegoły
        self.tree.bind("<Double-1>", self.on_double_click)

        # PRZYCISKI
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=10)

        btn_del_sel = ctk.CTkButton(btn_frame, text=self.txt["btn_del_selected"], command=self.delete_selected,
                                    **self.btn_style)
        btn_del_sel.pack(side="left", padx=5)

        btn_del_all = ctk.CTkButton(btn_frame, text=self.txt["btn_clear_archive"], command=self.delete_all_archive,
                                    **self.btn_style)
        btn_del_all.configure(fg_color="#e74c3c", hover_color="#c0392b")
        btn_del_all.pack(side="left", padx=5)

        btn_close = ctk.CTkButton(btn_frame, text=self.txt["btn_close"], command=self.win.destroy, **self.btn_style)
        btn_close.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        btn_close.pack(side="left", padx=5)

        self.refresh_list()

    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        today = date.today()

        # SQL: Pobranie wszystkich egzaminów z bazy
        # Konwersja na dict dla łatwiejszego operowania (sqlite3.Row -> dict)
        all_exams = [dict(e) for e in self.storage.get_exams()]

        active_exams = []
        arch_exams = []

        for exam in all_exams:
            if date_format(exam["date"]) >= today:
                active_exams.append(exam)
            else:
                arch_exams.append(exam)

        active_exams.sort(key=lambda x: x["date"])
        arch_exams.sort(key=lambda x: x["date"], reverse=True)

        display_exams = active_exams + arch_exams

        for exam in display_exams:
            exam_date = date_format(exam["date"])
            days = (exam_date - today).days

            status_txt = ""
            tag = "normal"

            if days < 0:
                status_txt = self.txt["tag_archived"]
                tag = "past"
            elif days == 0:
                status_txt = self.txt["tag_today"]
                tag = "active"
            else:
                status_txt = self.txt["tag_x_days"].format(days=days)
                tag = "active"

            # SQL: Pobranie tematów dla konkretnego egzaminu
            topics_rows = self.storage.get_topics(exam["id"])
            topics = [dict(t) for t in topics_rows]

            total = len(topics)
            done = len([t for t in topics if t["status"] == "done"])
            progress_str = f"{done} / {total}"

            self.tree.insert("", "end", iid=exam["id"],
                             values=(exam["date"], exam["subject"], exam["title"], status_txt, progress_str),
                             tags=(tag,))

    def delete_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_del"])
            return

        exam_id = selection[0]

        # SQL: Pobranie danych do potwierdzenia (szukamy na liście pobranej z bazy)
        all_exams = self.storage.get_exams()
        name = "ten egzamin"
        type_of_exam = "element"

        for e in all_exams:
            if e["id"] == exam_id:
                name = e["subject"]
                type_of_exam = e["title"]
                break

        confirm = messagebox.askyesno(self.txt["msg_warning"],
                                      self.txt["msg_confirm_del_perm"].format(type=type_of_exam, name=name))
        if confirm:
            # SQL: Usunięcie egzaminu (tematy usuną się kaskadowo w bazie)
            self.storage.delete_exam(exam_id)

            self.refresh_list()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_archived_del"])

    def delete_all_archive(self):
        today = date.today()

        # SQL: Sprawdzenie czy są przeszłe egzaminy
        all_exams = self.storage.get_exams()
        has_past = any(date_format(e["date"]) < today for e in all_exams)

        if not has_past:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_no_archive"])
            return

        confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_clear_archive"])
        if confirm:
            ids_to_remove = [e["id"] for e in all_exams if date_format(e["date"]) < today]

            # SQL: Iteracyjne usuwanie (StorageManager robi commit per delete lub można by to zoptymalizować,
            # ale delete_exam jest bezpieczne)
            for eid in ids_to_remove:
                self.storage.delete_exam(eid)

            self.refresh_list()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_archive_cleared"])

    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        exam_id = selection[0]
        # SQL: Pobranie konkretnego egzaminu z bazy
        all_exams = self.storage.get_exams()
        selected_exam_row = next((e for e in all_exams if e["id"] == exam_id), None)

        if selected_exam_row:
            # Konwersja na dict dla okna szczegółów
            self.open_details_window(dict(selected_exam_row))

    # --- OKNO SZCZEGÓŁÓW ---
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

        # --- PASEK AKCJI (Notatnik + Postęp) ---
        action_frame = ctk.CTkFrame(hist_window, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(0, 5))

        # 1. Przycisk Notatnik (Lewa strona) - ZMIANA STYLU
        # Usunięto emotkę i zmieniono styl na transparentny z ramką
        btn_notebook = ctk.CTkButton(action_frame,
                                     text=self.txt.get('btn_notebook', 'Notatnik'),
                                     height=28, width=100,
                                     fg_color="transparent", border_width=1, border_color="gray",
                                     text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                                     command=lambda: NotebookWindow(hist_window, self.txt,
                                                                    self.btn_style, exam_data,
                                                                    storage=self.storage))
        btn_notebook.pack(side="left")

        # 2. Label Postępu (Prawa strona)
        lbl_progress = ctk.CTkLabel(action_frame, text="", font=("Arial", 13, "bold"))
        lbl_progress.pack(side="right")
        # ---------------------------------------

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

            # SQL: Pobranie tematów dla konkretnego egzaminu
            topics_rows = self.storage.get_topics(exam_data["id"])
            exam_topics = [dict(t) for t in topics_rows]

            exam_topics.sort(key=lambda x: str(x.get("scheduled_date") or "9999-99-99"))

            total = len(exam_topics)
            done = len([t for t in exam_topics if t["status"] == "done"])
            pct = int((done / total) * 100) if total > 0 else 0

            prog_txt = self.txt.get("col_progress", "Postęp")

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
            # SQL: Pobranie tematów by znaleźć właściwy
            topics_rows = self.storage.get_topics(exam_data["id"])
            topic_row = next((t for t in topics_rows if t["id"] == topic_id), None)

            if topic_row:
                # Konwersja na dict, by móc edytować
                topic = dict(topic_row)
                topic["status"] = "done" if topic["status"] == "todo" else "todo"

                # SQL: Zapis zmian w bazie
                self.storage.update_topic(topic)

                refresh_details()
                self.refresh_list()

                # --- POPRAWKA: Sprawdź osiągnięcia po zmianie statusu w archiwum ---
                if self.dashboard_callback:
                    self.dashboard_callback()

        def edit_topic_local():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_topic"])
                return

            topic_id = selected[0]
            # SQL: Pobranie tematu
            topics_rows = self.storage.get_topics(exam_data["id"])
            topic_row = next((t for t in topics_rows if t["id"] == topic_id), None)

            if topic_row:
                # Przekazujemy dict do funkcji edycji
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

        btn_edit = ctk.CTkButton(btn_frame, text=self.txt["btn_edit_exam"], command=edit_exam_local,
                                 **self.btn_style)
        btn_edit.pack(side="left", padx=5)

        btn_close = ctk.CTkButton(btn_frame, text=self.txt["btn_close"], command=hist_window.destroy,
                                  **self.btn_style)
        btn_close.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        btn_close.pack(side="left", padx=5)