import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date
from core.storage import save
from core.planner import plan, date_format
from gui.windows.add_exam import AddExamWindow
from gui.windows.archive import ArchiveWindow
from gui.windows.edit import select_edit_item, EditExamWindow, EditTopicWindow

class PlanWindow():
    def __init__(self, parent, txt, data, btn_style, dashboard_callback):
        self.parent = parent
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback

        #ustawienie okna
        # self.win = tk.Toplevel(parent)
        # self.win.geometry("800x450")
        # self.win.title(self.txt["win_plan_title"])

        self.win = parent

        #ramka
        frame = tk.Frame(self.win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # konfiguracja tabeli
        columns = ("data", "przedmiot", "temat")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("data", text=self.txt["col_date"])
        self.tree.column("data", width=100, anchor="center")
        self.tree.heading("przedmiot", text=self.txt["col_subject"])
        self.tree.column("przedmiot", width=150, anchor="w")
        self.tree.heading("temat", text=self.txt["col_topic_long"])
        self.tree.column("temat", width=300, anchor="w")

        # tagi dla kolorów
        self.tree.tag_configure("exam", foreground="red", font=("Arial", 13, "bold"))
        self.tree.tag_configure("done", foreground="green", font=("Arial", 12, "bold"))
        self.tree.tag_configure("date_header", font=("Arial", 13, "bold"))
        self.tree.tag_configure("todo", font=("Arial", 13, "bold"))
        self.tree.tag_configure("normal", font=("Arial", 12, "bold"))
        self.tree.tag_configure("today", font=("Arial", 12, "bold"), foreground="violet")
        self.tree.tag_configure("red", font=("Arial", 13, "bold"), foreground="red")
        self.tree.tag_configure("orange", font=("Arial", 12, "bold"), foreground="orange")
        self.tree.tag_configure("yellow", foreground="yellow", font=("Arial", 12, "bold"))
        self.tree.tag_configure("overdue", foreground="gray", font=("Arial", 12, "italic", "bold"))

        # scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<Button-1>", self.on_tree_click)

        #   PRZYCISKI W 2 RZEDACH
        # btn_frame1 = tk.Frame(self.win)
        # btn_frame1.pack(pady=0)
        #
        # btn_frame2 = tk.Frame(self.win)
        # btn_frame2.pack(pady=5)
        #
        # btn_refresh = tk.Button(btn_frame1, text=self.txt["btn_refresh"], command=self.refresh_table, **self.btn_style)
        # btn_refresh.pack(side="left", padx=5)
        # btn_gen = tk.Button(btn_frame1, text=self.txt["btn_gen_plan"], command=self.run_and_refresh, **self.btn_style)
        # btn_gen.pack(side="left", padx=5)
        # btn_toggle = tk.Button(btn_frame1, text=self.txt["btn_toggle_status"], command=self.toggle_status, **self.btn_style)
        # btn_toggle.pack(side="left", padx=5)
        # btn_add = tk.Button(btn_frame1, text=self.txt["btn_add_exam"], command=self.open_add_window, **self.btn_style)
        # btn_add.pack(side="left", padx=5)
        #
        # btn_edit = tk.Button(btn_frame2, text=self.txt["btn_edit"], command=self.open_edit, **self.btn_style)
        # btn_edit.pack(side="left", padx=5)
        # btn_archive = tk.Button(btn_frame2, text=self.txt["btn_all_exams"], command=self.open_archive, **self.btn_style)
        # btn_archive.pack(side="left", padx=5)
        # btn_clear = tk.Button(btn_frame2, text=self.txt["btn_clear_data"], command=self.clear_database, **self.btn_style, foreground="red")
        # btn_clear.pack(side="left", padx=5)
        # btn_close = tk.Button(btn_frame2, text=self.txt["btn_close"], command=self.win.destroy, **self.btn_style, activeforeground="red")
        # btn_close.pack(side="left", padx=5)

        # pierwsze odswiezenia tabeli
        self.refresh_table()

    def on_tree_click(self, event):
        # Sprawdzamy, w który wiersz kliknięto
        item_id = self.tree.identify_row(event.y)

        if not item_id:
            # Kliknięto w puste białe tło pod tabelą -> odznacz wszystko
            self.deselect_all()
            return

        tags = self.tree.item(item_id, "tags")
        values = self.tree.item(item_id, "values")

        # WARUNEK 1: Czy to nagłówek daty?
        if "date_header" in tags:
            return "break"  # "break" przerywa zdarzenie - zaznaczenie się nie uda

        # WARUNEK 2: Czy to pusta linia (separator)?
        # Sprawdzamy czy pierwszy element values jest pusty lub jest znakiem "^" (używanym jako odstęp)
        # Oraz czy nie ma ID tematu/egzaminu (tematy mają iid="topic_...", egzaminy "exam_...")
        if not values or values[0] == "" or values[0] == "^" or "active" in tags or "past" in tags:
            # Sprawdźmy czy to nie jest nagłówek "ZALEGŁE" (on ma tag overdue, ale nie ma ID)
            # Najprościej: jeśli nie ma ID w bazie (item_id nie zaczyna się od 'exam_' ani 'topic_') to blokuj
            if not (item_id.startswith("exam_") or item_id.startswith("topic_")):
                return "break"

    def deselect_all(self):
        selection = self.tree.selection()
        if selection:
            self.tree.selection_remove(selection)

    # funkcja odswiezajaca tabele
    def refresh_table(self):
        # wyczyszczenie tabeli
        for item in self.tree.get_children():
            self.tree.delete(item)

        #   ZALEGŁE TEMATY
        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= date.today()}
        overdue_topics = [
            t for t in self.data["topics"]
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < date.today()
               and t["status"] == "todo" and t["exam_id"] in active_exams_ids
        ]

        # wstawienie zaleglych tematow do tabeli jako pierwsze
        if overdue_topics:
            self.tree.insert("", "end", values=(self.txt["tag_overdue"], "", ""), tags=("overdue",))
            for topic in overdue_topics:
                subj_name = self.txt["val_other"]
                for exam in self.data["exams"]:
                    if exam["id"] == topic["exam_id"]:
                        subj_name = exam["subject"]
                        break
                self.tree.insert("", "end", iid=topic["id"], values=(topic["scheduled_date"], subj_name, topic["name"]), tags=("overdue",))
            self.tree.insert("", "end", values=("", "", ""))

        #   DATY I PLAN NA PRZYSZŁOŚĆ
        all_dates = set()
        for exam in self.data["exams"]:
            if date_format(exam["date"]) >= date.today():
                all_dates.add(str(exam["date"]))
        for topic in self.data["topics"]:
            if topic["scheduled_date"] and date_format(topic["scheduled_date"]) >= date.today():
                all_dates.add(str(topic["scheduled_date"]))

        sorted_dates = sorted(list(all_dates))

        for day_str in sorted_dates:
            date_printed = False

            # funkcja pomocnicza do nagłówka daty
            def print_date_header():
                nonlocal date_printed
                if not date_printed:
                    days_left = (date_format(day_str) - date.today()).days
                    display_text = ""
                    tag = "normal"

                    if days_left == 0:
                        display_text = self.txt["tag_today"]
                        tag = "today"
                    elif days_left == 1:
                        display_text = self.txt["tag_1_day"]
                        tag = "red"
                    else:
                        display_text = self.txt["tag_x_days"].format(days=days_left)
                        if days_left <= 3:
                            tag = "orange"
                        elif days_left <= 6:
                            tag = "yellow"

                    self.tree.insert("", "end", values=(day_str, "", ""), tags=("date_header",))
                    self.tree.insert("", "end", values=(display_text, "", ""), tags=("date_header", tag))
                    date_printed = True

            # egzaminy w tym dniu
            for exam in self.data["exams"]:
                if exam["date"] == day_str:
                    print_date_header()
                    self.tree.insert("", "end", iid=exam["id"], values=("|", exam["subject"], exam["title"]), tags=("exam",))

            # tematy w tym dniu
            for topic in self.data["topics"]:
                if str(topic.get("scheduled_date")) == day_str:
                    subj_name = self.txt["val_other"]
                    for exam in self.data["exams"]:
                        if exam["id"] == topic["exam_id"]:
                            subj_name = exam["subject"]
                            break
                    print_date_header()
                    self.tree.insert("", "end", iid=topic["id"], values=("|", subj_name, topic["name"]), tags=(topic["status"],))

            if date_printed:
                self.tree.insert("", "end", values=("^", "", ""))

    # funkcja dla przycisku generuj plan | generuje a nastepnie odswieza plan | jesli wystapi blad to go pokaze
    def run_and_refresh(self):
        try:
            plan(self.data)
            save(self.data)
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_plan_done"])
        except Exception as e:
            messagebox.showerror(self.txt["msg_error"], f"Error: {e}")

    # funkcja zmieniajaca status zadania
    def toggle_status(self):
        #znalezienie zaznaczonego id
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_status"])
            return

        topic_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if t["id"] == topic_id), None)

        #zmiana statusu i zapisanie
        if target_topic:
            target_topic["status"] = "done" if target_topic["status"] == "todo" else "todo"
            save(self.data)

            # odswiezenie widoku
            new_tag = target_topic["status"]
            self.tree.item(topic_id, tags=(new_tag,))

            if self.dashboard_callback: self.dashboard_callback()
        else:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_cant_status"])

    # funkcja czyszczaca baze danych
    def clear_database(self):
        # potwierdzenie od uzytkownika
        if messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_clear_db"]):
            #ustawienie bazy na dane poczatkowe
            current_lang = self.data["settings"].get("lang", "en")
            self.data["exams"] = []
            self.data["topics"] = []
            self.data["settings"] = {
                "max_per_day": 2,
                "max_same_subject_per_day": 1,
                "lang": current_lang
            }
            save(self.data) # zapisanie
            self.refresh_table() # odswiezenie
            if self.dashboard_callback: self.dashboard_callback() # callback dla odswiezenia
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_db_cleared"])

    #   DO OTWIERANIA INNYCH OKIEN

    # funkcja otwierajaca okno dodawania egzaminu
    def open_add_window(self):
        # callback po dodaniu odswiezajacy tabele i dashboard
        def on_add():
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

        AddExamWindow(self.win, self.txt, self.data, self.btn_style, callback=on_add)

    # funkcja otwierajaca okno edycji
    def open_edit(self):
        # callback po edycji odswiezy tabele
        def on_edit():
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

        select_edit_item(self.win, self.data, self.txt, self.tree, self.btn_style, callback=on_edit)

    # funkcja otwierajaca okno archiwum
    def open_archive(self):
        # w oknie archiwum sa przyciski do edycji, wiec przekazuje im te funkcje
        def edit_exam_wrapper(exam_data, callback):
            EditExamWindow(self.win, self.txt, self.data, self.btn_style, exam_data, callback)

        def edit_topic_wrapper(topic_data, callback):
            EditTopicWindow(self.win, self.txt, self.data, self.btn_style, topic_data, callback)

        # archiwum po usunięciu też powinno odświeżyć dashboard
        archive_dashboard_cb = self.dashboard_callback

        ArchiveWindow(self.win, self.txt, self.data, self.btn_style, edit_exam_func=edit_exam_wrapper, edit_topic_func=edit_topic_wrapper)