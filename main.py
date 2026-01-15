import tkinter as tk
from tkinter import messagebox, ttk
from core.storage import load, save, load_language
from core.planner import plan, date_format
from datetime import date
from gui.windows.add_exam import AddExamWindow
from gui.windows.manual import ManualWindow
from gui.windows.archive import ArchiveWindow
from gui.windows.edit import EditExamWindow, EditTopicWindow, select_edit_item

class GUI:
    #FUNKCJA WYKONUJĄCA SIE NA POCZĄTKU
    #launcher z szybkim podgladem i przyciskami do uruchomienia instrukcji i reszty programu
    def __init__(self, root):
        self.root = root

        self.data = load()  # Zaladowanie danych z pliku(funkcja z storage.py)

        #   pobranie i ustawienie jezyka programu
        current_lang_code = self.data["settings"].get("lang", "en")
        self.txt = load_language(current_lang_code)

        self.root.title(self.txt["app_title"])
        #self.root.geometry("400x500")
        self.root.resizable(False, False)

        # print(f"Loaded exams: {len(self.data["exams"])}")

        #   SEKCJA STATYSTYK
        # zbieranie danych do szybkiego podgladu
        today = date.today()

        active_exams_ids = {e["id"] for e in self.data["exams"]if date_format(e["date"]) >= today}
        active_topics = [t for t in self.data["topics"] if t["exam_id"] in active_exams_ids]

        total_topics = len(active_topics)
        done_topics = len([t for t in active_topics if t["status"] == "done"])

        progress = 0
        if total_topics > 0:
            progress = int((done_topics / total_topics) * 100)

        today_all_topics = [t for t in self.data["topics"] if str(t.get("scheduled_date")) == str(today)]
        today_total = len(today_all_topics)
        today_done = len([t for t in today_all_topics if t["status"] == "done"])

        today_prog = 0
        today_txt_2 = ""
        if today_total > 0:
            today_prog = int((today_done / today_total) * 100)
            #wzor w pliku jezykowym json: "postep dzisiaj: {done}/{total} ({prog}%)
            today_txt_2 = self.txt["stats_progress_today"].format(done=today_done, total=today_total, prog=today_prog)
        else:
            today_txt_2 = self.txt["stats_no_today"]

        topics_today = [t for t in self.data["topics"] if t["scheduled_date"] and str(t["scheduled_date"]) == str(today) and t["status"] == "todo"]
        count_today = len(topics_today)

        #   szukanie najblizszego egzaminu
        future_exams = [e for e in self.data["exams"] if date_format(e["date"]) >= today]
        future_exams.sort(key=lambda x: x["date"])
        next_exam_txt = self.txt["stats_no_upcoming"]
        days_color = "green"

        if future_exams:
            nearest = future_exams[0]
            days = (date_format(nearest["date"]) - today).days

            if days == 0:
                next_exam_txt = self.txt["stats_exam_today"].format(subject=nearest["subject"])
                days_color = "violet"
            elif days <= 2:
                if days == 1:
                    next_exam_txt = self.txt["stats_exam_tomorrow"].format(subject=nearest["subject"])
                else:
                    next_exam_txt = self.txt["stats_exam_days"].format(days=days, subject=nearest["subject"])
                days_color = "orange"
            elif days <= 5:
                next_exam_txt = self.txt["stats_exam_days"].format(days=days, subject=nearest["subject"])
                days_color = "yellow"
            else:
                next_exam_txt = self.txt["stats_exam_days"].format(days=days, subject=nearest["subject"])

        #ustawienie tytulu za pomoca biblioteki tkinter
        self.label_title = tk.Label(self.root, text=self.txt["app_title"], font=("Arial", 20, "bold"))
        self.label_title.pack(pady=(20, 10))

        #tkinter ustawienie ramki na szybki podglad i wstawienie danych do okna
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(fill="x", padx=40, pady=10, ipady=10)

        tk.Label(stats_frame, text=next_exam_txt, font=("Arial", 13, "bold"), foreground=days_color).pack(pady=2)

        # today_txt = f"Zadania na dziś: {count_today}"
        # tk.Label(stats_frame, text=today_txt, font=("Arial", 12, "bold")).pack(pady=2)

        lbl_today = tk.Label(stats_frame, text=today_txt_2, font=("Arial", 12, "bold"))
        if today_prog == 100:
            lbl_today.config(foreground="green")
        lbl_today.pack(pady=2)

        progress_txt = self.txt["stats_total_progress"].format(done=done_topics, total=total_topics, progress=progress)
        tk.Label(stats_frame, text=progress_txt, font=("Arial", 12, "bold")).pack(pady=5)

        # STYL PRZYCISKOW DLA CALEGO PROGRAMU
        # zrobione aby sie nie powtarzac za kazdym razem przy tworzeniu przyciskow
        self.btn_style = {
            "font": ("Arial", 11, "bold"),
            "cursor": "hand2",
            "height": 2,
            "width": 18,
            "relief": "flat",
            "bg": "#e1e1e1"
        }

        # PRZYCISKI W MENU GLOWNYM
        self.label_title = tk.Label(self.root, text=self.txt["menu_title"], font=("Arial", 14, "bold"))
        self.label_title.pack(pady=20, padx=60)
        self.btn_week = tk.Button(self.root, text=self.txt["btn_run"], command=self.show_plan, **self.btn_style)
        self.btn_week.pack(pady=10)
        self.btn_manual = tk.Button(self.root, text=self.txt["btn_manual"], command=self.manual, **self.btn_style)
        self.btn_manual.pack(pady=10)
        self.btn_exit = tk.Button(self.root, text=self.txt["btn_exit"], command=self.root.quit, **self.btn_style, activeforeground="red")
        self.btn_exit.pack(pady=40)

        # WYBOR JEZYKA
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.lang_map = {"English": "en", "Polski": "pl"}
        self.lang_rev = {v: k for k, v in self.lang_map.items()}  # odwrocenie slownika aby znalezc nazwe po kodzie

        self.combo_lang = ttk.Combobox(bottom_frame, values=list(self.lang_map.keys()), state="readonly", width=10)
        current_lang_name = self.lang_rev.get(current_lang_code, "English")
        self.combo_lang.set(current_lang_name)
        self.combo_lang.pack(side="right")

        def language_change(event):
            selected_name = self.combo_lang.get()
            new_code = self.lang_map[selected_name]

            if new_code != self.data["settings"].get("lang", "en"):
                self.data["settings"]["lang"] = new_code
                save(self.data)
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_lang_changed"])

        self.combo_lang.bind("<<ComboboxSelected>>", language_change)

    #OKNO Z INSTRUKCJĄ
    def manual(self):
        ManualWindow(self.root, self.txt, self.btn_style)

    #FUNKCJA URUCHAMIAJĄCA PROGRAM PLANUJĄCY
    def run_planner(self):
        try:
            plan(self.data)
            save(self.data)
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_plan_done"])
        except Exception as e:
            messagebox.showerror(self.txt["msg_error"], f"Error: {e}")

    #OKNO DO DODAWANIA NOWYCH EGZAMINOW I TEMATÓW
    def add_window(self, callback=None):
        AddExamWindow(self.root, self.txt, self.data, self.btn_style, callback)

    #FUNKCJE DO EDYCJI DANYCH   ------------
    #   SPRAWDZENIE CO JEST ZAZNACZONE
    def edit_select(self, tree, callback=None):
        select_edit_item(self.root, self.data, self.txt, tree, self.btn_style, callback)

    def edit_exam_window(self, exam_data, callback=None):
        EditExamWindow(self.root, self.txt, self.data, self.btn_style, exam_data, callback)

    def edit_topic_window(self, topic_data, callback=None):
        EditTopicWindow(self.root, self.txt, self.data, self.btn_style, topic_data, callback)
    #                           ------------

    #OKNO Z GOTOWYM PLANEM NAUKI
    def show_plan(self):
        week_win = tk.Toplevel(self.root)
        week_win.geometry("800x450")
        week_win.title(self.txt["win_plan_title"])

        frame = tk.Frame(week_win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # naglowki tabeli
        columns = ("data", "przedmiot", "temat")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("data", text=self.txt["col_date"])
        tree.column("data", width=100, anchor="center")
        tree.heading("przedmiot", text=self.txt["col_subject"])
        tree.column("przedmiot", width=150, anchor="w")
        tree.heading("temat", text=self.txt["col_topic_long"])
        tree.column("temat", width=300, anchor="w")

        # tagi glownie dla kolorow
        tree.tag_configure("exam", foreground="red", font=("Arial", 13, "bold"))
        tree.tag_configure("done", foreground="green", font=("Arial", 12, "bold"))
        tree.tag_configure("date_header", font=("Arial", 13, "bold"))
        tree.tag_configure("todo", font=("Arial", 13, "bold"))
        tree.tag_configure("normal", font=("Arial", 12, "bold"))
        tree.tag_configure("today", font=("Arial", 12, "bold"), foreground="violet")
        tree.tag_configure("red", font=("Arial", 13, "bold"), foreground="red")
        tree.tag_configure("orange", font=("Arial", 12, "bold"), foreground="orange")
        tree.tag_configure("yellow", foreground="yellow", font=("Arial", 12, "bold"))
        tree.tag_configure("overdue", foreground="gray", font=("Arial", 12, "italic", "bold"))

        # dzialanie scrolla
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        # FUNKCJA WEW. ODSWIEZAJACA WIDOK PLANU
        def refresh_table():
            for item in tree.get_children():
                tree.delete(item)

            #       ZALEGLE TEMATY

            active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= date.today()}

            #   pobranie zaleglych tematow
            overdue_topics = [t for t in self.data["topics"] if t.get("scheduled_date") and date_format(t["scheduled_date"]) < date.today() and t["status"] == "todo" and t["exam_id"] in active_exams_ids]
            if overdue_topics:
                tree.insert("", "end", values=(self.txt["tag_overdue"]), tags=("overdue",))
                for topic in overdue_topics:
                    subj_name = self.txt["val_other"]
                    for exam in self.data["exams"]:
                        if exam["id"] == topic["exam_id"]:
                            subj_name = exam["subject"]
                            break
                    tree.insert("", "end", iid=topic["id"], values=(topic["scheduled_date"], subj_name, topic["name"]), tags=("overdue",))
                tree.insert("", "end", values=("", "", ""))

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
                def print_date():
                    nonlocal date_printed
                    if not date_printed:
                        tree.insert("", "end", values=(day_str, "", ""), tags=("date_header",))
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

                        tree.insert("", "end", values=(display_text, "", ""), tags=(tag,))
                        date_printed = True

                for exam in self.data["exams"]:
                    if exam["date"] == day_str:
                        print_date()
                        tree.insert("", "end", iid=exam["id"], values=("", exam["subject"], exam["title"]), tags=("exam",))
                for topic in self.data["topics"]:
                    if str(topic.get("scheduled_date")) == day_str:
                        subj_name = self.txt["val_other"]
                        for exam in self.data["exams"]:
                            if exam["id"] == topic["exam_id"]:
                                subj_name = exam["subject"]
                                break
                        print_date()
                        current_status = topic["status"]
                        tree.insert("", "end", iid=topic["id"], values=("", subj_name, topic["name"]), tags=(current_status,))
                tree.insert("", "end", values=("", "", ""))

        refresh_table()

        # FUNKCJA WEW. ZMIENIAJACA STATUS ZADANIA
        def toggle_status():
            seleted_item = tree.selection()
            if not seleted_item:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_status"])
                return
            topic_id = seleted_item[0]
            target_topic = None
            for topic in self.data["topics"]:
                if topic["id"] == topic_id:
                    target_topic = topic
                    break

            if target_topic:
                if target_topic["status"] == "todo":
                    target_topic["status"] = "done"
                    tree.item(topic_id, tags=("done",))
                else:
                    target_topic["status"] = "todo"
                    tree.item(topic_id, tags=("todo",))
                save(self.data)
            else:
                messagebox.showwarning(self.txt["msg_error"], self.txt["msg_cant_status"])

        # FUNKCJA WEW. USUWAJACA DANE Z BAZY
        def clear_database():
            answer = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_clear_db"])
            if answer:
                current_lang = self.data["settings"].get("lang", "en")
                self.data = {
                    "settings": {
                        "max_per_day": 2,
                        "max_same_subject_per_day": 1,
                        "lang": current_lang
                    },
                    "exams": [],
                    "topics": []
                }
                save(self.data)
                refresh_table()
                messagebox.showinfo(self.txt["msg_success"], self.txt["msg_db_cleared"])

        def run_and_refresh():
            self.run_planner()
            refresh_table()

        btn_frame1 = tk.Frame(week_win)
        btn_frame1.pack(pady=0)

        btn_frame2 = tk.Frame(week_win)
        btn_frame2.pack(pady=5)

        btn_refresh = tk.Button(btn_frame1, text=self.txt["btn_refresh"], command=refresh_table, **self.btn_style)
        btn_refresh.pack(side="left", padx=5)

        btn_gen = tk.Button(btn_frame1, text=self.txt["btn_gen_plan"], command=run_and_refresh, **self.btn_style)
        btn_gen.pack(side="left", padx=5)

        btn_toggle = tk.Button(btn_frame1, text=self.txt["btn_toggle_status"], command=toggle_status, **self.btn_style)
        btn_toggle.pack(side="left", padx=5)

        btn_add = tk.Button(btn_frame1, text=self.txt["btn_add_exam"], command=lambda: self.add_window(callback=refresh_table), **self.btn_style)
        btn_add.pack(side="left", padx=5)

        btn_edit = tk.Button(btn_frame2, text=self.txt["btn_edit"], command=lambda: self.edit_select(tree, callback=refresh_table), **self.btn_style)
        btn_edit.pack(side="left", padx=5)

        btn_archive = tk.Button(btn_frame2, text=self.txt["btn_all_exams"], command=self.archive_window, **self.btn_style)
        btn_archive.pack(side="left", padx=5)

        btn_clear = tk.Button(btn_frame2, text=self.txt["btn_clear_data"], command=clear_database, **self.btn_style, foreground="red")
        btn_clear.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame2, text=self.txt["btn_close"], command=week_win.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="left", padx=5)

    #OKNO ARCHIWUM
    def archive_window(self):
        ArchiveWindow(self.root, self.txt, self.data, self.btn_style, edit_exam_func=self.edit_exam_window, edit_topic_func=self.edit_topic_window)



if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()
