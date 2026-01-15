import tkinter as tk
from tkinter import messagebox, ttk
from storage import load, save, load_language
from planner import plan, date_format
import uuid
from datetime import datetime, timedelta, date
from tkcalendar import DateEntry

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
        man_win = tk.Toplevel(self.root)
        #man_win.geometry("450x500")
        man_win.title(self.txt["manual_title"])

        frame = tk.Frame(man_win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, padx=10, pady=10)
        text.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=text.yview)

        text.tag_config("bold", font=("Arial", 20, "bold"))
        text.tag_config("normal", font=("Arial", 13))

        text.insert("end", self.txt["manual_header"], "bold")
        text.insert("end", self.txt["manual_content"], "normal")
        text.configure(state="disabled")
        btn_close = tk.Button(man_win, text=self.txt["btn_close"], command=man_win.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="bottom", pady=10)

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
        # FUNKCJA WEW. ZAPISUJACA DANE WPROWADZONE PRZEZ UZYTKOWNIKA
        def save_new_exam():
            subject = entry_subject.get()
            date_str = entry_date.get()
            title = entry_title.get()
            topics = text_topics.get("1.0", tk.END)

            if not subject or not date_str or not title:
                messagebox.showwarning(self.txt["msg_error"], self.txt["msg_fill_fields"])
                return

            topics_list = [t.strip() for t in topics.split("\n") if t.strip()]
            exam_id = f"exam_{uuid.uuid4().hex[:8]}"

            new_exam = {
                "id": exam_id,
                "subject": subject,
                "title": title,
                "date": date_str,
            }
            self.data["exams"].append(new_exam)

            for topic in topics_list:
                self.data["topics"].append({
                    "id": f"topic_{uuid.uuid4().hex[:8]}",
                    "exam_id": exam_id,
                    "name": topic,
                    "status": "todo",
                    "scheduled_date": None,
                    "locked": False
                })

            save(self.data)

            if callback:
                callback()

            add_win.destroy()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_added"].format(count=len(topics_list)))

        add_win = tk.Toplevel(self.root)
        #add_win.geometry("460x400")
        add_win.resizable(False, False)
        add_win.title(self.txt["win_add_title"])

        tk.Label(add_win, text=self.txt["form_subject"]).grid(row=0, column=0, pady=10, padx=10, sticky="e")
        entry_subject = tk.Entry(add_win, width=30)
        entry_subject.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(add_win, text=self.txt["form_type"]).grid(row=1, column=0, pady=10, padx=10, sticky="e")
        entry_title = tk.Entry(add_win, width=30)
        entry_title.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(add_win, text=self.txt["form_date"]).grid(row=2, column=0, pady=10, padx=10, sticky="e")
        entry_date = DateEntry(add_win, width=27, date_pattern='y-mm-dd')
        entry_date.grid(row=2, column=1, padx=10, pady=10)
        tomorrow = datetime.now() + timedelta(days=1)
        entry_date.set_date(tomorrow)

        tk.Label(add_win, text=self.txt["form_topics_add"]).grid(row=3, column=0, columnspan=2, pady=5)
        text_topics = tk.Text(add_win, width=40, height=10)
        text_topics.grid(row=4, column=0, columnspan=2, padx=10)

        btn_frame = tk.Frame(add_win)
        btn_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=20)

        btn_save = tk.Button(btn_frame, text=self.txt["btn_save"], command=save_new_exam, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_exit = tk.Button(btn_frame, text=self.txt["btn_cancel"], command=add_win.destroy, **self.btn_style, activeforeground="red")
        btn_exit.pack(side="left", padx=5)

    #FUNKCJE DO EDYCJI DANYCH   ------------
    #   SPRAWDZENIE CO JEST ZAZNACZONE
    def edit_select(self, tree, callback=None):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_edit"])
            return

        item_id = selected_item[0]

        for exam in self.data["exams"]:
            if exam["id"] == item_id:
                self.edit_exam_window(exam, callback)
                return

        for topic in self.data["topics"]:
            if topic["id"] == item_id:
                self.edit_topic_window(topic, callback)
                return

        messagebox.showerror(self.txt["msg_error"], self.txt["msg_cant_edit"])

    #   OKNO EDYCJI CALOSCI (EGZAMINU)
    def edit_exam_window(self, exam_data, callback=None):
        edit_win = tk.Toplevel(self.root)
        edit_win.resizable(False, False)
        edit_win.title(self.txt["win_edit_exam_title"].format(subject=exam_data["subject"]))

        tk.Label(edit_win, text=self.txt["form_subject"]).grid(row=0, column=0, pady=5, padx=10, sticky="e")
        ent_subject = tk.Entry(edit_win, width=30)
        ent_subject.insert(0, exam_data["subject"])
        ent_subject.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(edit_win, text=self.txt["form_type"]).grid(row=1, column=0, pady=5, padx=10, sticky="e")
        ent_title = tk.Entry(edit_win, width=30)
        ent_title.insert(0, exam_data["title"])
        ent_title.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(edit_win, text=self.txt["form_date"]).grid(row=2, column=0, pady=5, padx=10, sticky="e")
        ent_date = DateEntry(edit_win, width=27, date_pattern='y-mm-dd')
        ent_date.grid(row=2, column=1, padx=10, pady=5)
        if exam_data["date"]:
            ent_date.set_date(exam_data["date"])

        tk.Label(edit_win, text=self.txt["form_topics_edit"]).grid(row=3, column=0, pady=5, columnspan=2)
        txt_topics = tk.Text(edit_win, width=40, height=10)
        txt_topics.grid(row=4, column=0, columnspan=2, padx=10)
        topics_list = [t for t in self.data["topics"] if t["exam_id"] == exam_data["id"]]
        for t in topics_list:
            txt_topics.insert(tk.END, t["name"] + "\n")

        def save_changes():
            exam_data["subject"] = ent_subject.get()
            exam_data["date"] = ent_date.get()
            exam_data["title"] = ent_title.get()

            new_names = [line.strip() for line in txt_topics.get("1.0", tk.END).split("\n") if line.strip()]
            existing_map = {t["name"]: t for t in topics_list}

            topics_keep_ids = []

            for name in new_names:
                if name in existing_map:
                    topic = existing_map[name]
                    topics_keep_ids.append(topic["id"])
                else:
                    new_id = f"topic_{uuid.uuid4().hex[:8]}"
                    self.data["topics"].append({
                        "id": new_id,
                        "exam_id": exam_data["id"],
                        "name": name,
                        "status" : "todo",
                        "scheduled_date": None,
                        "locked": False
                    })
                    topics_keep_ids.append(new_id)

            self.data["topics"] = [
                t for t in self.data["topics"]
                if t["exam_id"] != exam_data["id"] or t["id"] in topics_keep_ids
            ]

            save(self.data)

            if callback:
                callback()

            edit_win.destroy()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_data_updated"])

        def delete_exam():
            confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_exam"].format(subject=exam_data["subject"]))
            if confirm:
                self.data["topics"] = [t for t in self.data["topics"] if t["exam_id"] != exam_data["id"]]
                self.data["exams"] = [e for e in self.data["exams"] if e["id"] != exam_data["id"]]

                save(self.data)

                if callback:
                    callback()

                edit_win.destroy()
                messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_deleted"])

        btn_frame = tk.Frame(edit_win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        btn_save = tk.Button(btn_frame, text=self.txt["btn_save_changes"], command=save_changes, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_delete = tk.Button(btn_frame, text=self.txt["btn_delete"], command=delete_exam, **self.btn_style, foreground="red")
        btn_delete.pack(side="left", padx=5)

        btn_cancel = tk.Button(btn_frame, text=self.txt["btn_cancel"], command=edit_win.destroy, **self.btn_style, activeforeground="red")
        btn_cancel.pack(side="left", padx=5)

    #   OKNO EDYCJI TEMATU
    def edit_topic_window(self, topic_data, callback=None):
        topic_win = tk.Toplevel(self.root)
        topic_win.title(self.txt["win_edit_topic_title"].format(name=topic_data["name"]))
        topic_win.resizable(width=False, height=False)

        tk.Label(topic_win, text=self.txt["form_topic"]).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        ent_name = tk.Entry(topic_win, width=30)
        ent_name.insert(0, topic_data["name"])
        ent_name.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(topic_win, text=self.txt["form_date"]).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        ent_date = DateEntry(topic_win, width=27, date_pattern='y-mm-dd')
        ent_date.grid(row=1, column=1, padx=10, pady=10)
        original_date = topic_data.get("scheduled_date", "")
        if original_date:
            ent_date.set_date(original_date)

        is_locked = tk.BooleanVar(value=topic_data.get("locked", False))
        check_locked = tk.Checkbutton(topic_win, text=self.txt["form_lock"], variable=is_locked, onvalue=True, offvalue=False)
        check_locked.grid(row=2, column=0, columnspan=2, pady=5)

        def save_changes():
            new_name = ent_name.get()
            new_date = ent_date.get()

            if not new_name:
                messagebox.showwarning(self.txt["msg_error"], self.txt["msg_topic_name_req"])
                return

            topic_data["name"] = new_name

            if not new_date.strip():
                topic_data["scheduled_date"] = None
            else:
                topic_data["scheduled_date"] = new_date

                if str(original_date) != new_date:
                    pass

            topic_data["locked"] = is_locked.get()

            infomess = self.txt["btn_refresh"]

            if new_date and str(original_date) != new_date:
                topic_data["locked"] = True
                infomess = self.txt["msg_topic_date_lock"]

            save(self.data)

            if callback:
                callback()

            topic_win.destroy()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_updated"].format(info=infomess))

        def delete_topic():
            confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_topic"])
            if confirm:
                self.data["topics"] = [t for t in self.data["topics"] if t["id"] != topic_data["id"]]
                save(self.data)

                if callback:
                    callback()

                topic_win.destroy()
                messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_deleted"])

        btn_frame = tk.Frame(topic_win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        btn_save = tk.Button(btn_frame, text=self.txt["btn_save"], command=save_changes, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_delete = tk.Button(btn_frame, text=self.txt["btn_delete"], command=delete_topic, **self.btn_style, foreground="red")
        btn_delete.pack(side="left", padx=5)

        btn_cancel = tk.Button(btn_frame, text=self.txt["btn_cancel"], command=topic_win.destroy, **self.btn_style, activeforeground="red")
        btn_cancel.pack(side="left", padx=5)
    #                           ------------

    #OKNO Z GOTOWYM PLANEM NAUKI
    def show_plan(self):
        week_win = tk.Toplevel(self.root)
        week_win.geometry("750x400")
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
            #   pobranie zaleglych tematow
            overdue_topics = [t for t in self.data["topics"] if t.get("scheduled_date") and date_format(t["scheduled_date"]) < date.today() and t["status"] == "todo"]
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
        arch_win = tk.Toplevel(self.root)
        arch_win.title(self.txt["win_archive_title"])

        tk.Label(arch_win, text=self.txt["msg_archive_header"], font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(arch_win, text=self.txt["msg_archive_sub"], font=("Arial", 12, "bold")).pack(pady=5)

        frame = tk.Frame(arch_win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ustawienie naglowkow tabeli
        columns = ("data", "przedmiot", "forma", "status")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        tree.heading("data", text=self.txt["col_date"])
        tree.column("data", width=100, anchor="center")
        tree.heading("przedmiot", text=self.txt["col_subject"])
        tree.column("przedmiot", width=180, anchor="w")
        tree.heading("forma", text=self.txt["col_form"])
        tree.column("forma", width=120, anchor="w")
        tree.heading("status", text=self.txt["col_status"])
        tree.column("status", width=150, anchor="center")

        # tagi dla kolorow
        tree.tag_configure("active", foreground="lightblue", font=("Arial", 12, "bold"))
        tree.tag_configure("past", foreground="gray", font=("Arial", 12, "bold"))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        today = date.today()

        def refresh_main_archive():
            for item in tree.get_children():
                tree.delete(item)

            all_exams = list(self.data["exams"])
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

                tree.insert("", "end", iid=exam["id"], values=(exam["date"], exam["subject"], exam["title"], status_txt), tags=(tag,))

        refresh_main_archive()

        #FUNKCJA USUWAJACA WYBRANY EGZAMIN
        def delete_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_del"])
                return

            exam_id = selection[0]

            name = "ten egzamin"
            for e in self.data["exams"]:
                if e["id"] == exam_id:
                    name = e["subject"]
                    break

            type_of_exam = "element"
            for t in self.data["exams"]:
                if t["id"] == exam_id:
                    type_of_exam = t["title"]
                    break

            confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_perm"].format(type=type_of_exam, name=name))
            if confirm:
                self.data["topics"] = [t for t in self.data["topics"] if t["exam_id"] != exam_id]
                self.data["exams"] = [e for e in self.data["exams"] if e["id"] != exam_id]

                save(self.data)

                refresh_main_archive()

                messagebox.showinfo(self.txt["msg_success"], self.txt["msg_archived_del"])

        #FUNKCJA USUWAJACA WSZYSTKIE ARCHIWALNE
        def delete_all_archive():
            nonlocal today
            has_past = any(date_format(e["date"]) < today for e in self.data["exams"])
            if not has_past:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_no_archive"])
                return

            confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_clear_archive"])
            if confirm:
                today = date.today()

                ids_to_remove = [e["id"] for e in self.data["exams"] if date_format(e["date"]) < today]

                self.data["exams"] = [e for e in self.data["exams"] if date_format(e["date"]) >= today]
                self.data["topics"] = [t for t in self.data["topics"] if t["exam_id"] not in ids_to_remove]

                save(self.data)

                refresh_main_archive()

                messagebox.showinfo(self.txt["msg_success"], self.txt["msg_archive_cleared"])

        #FUNKCJA OTWIERAJĄCA SZCZEGÓŁY
        def double_click(event):
            selection = tree.selection()
            if not selection:
                return

            exam_id = selection[0]

            selected_exam = next((e for e in self.data["exams"] if e["id"] == exam_id), None)
            if selected_exam:
                self.archive_datails_window(selected_exam, callback=refresh_main_archive)

        tree.bind("<Double-1>", double_click)

        btn_frame = tk.Frame(arch_win)
        btn_frame.pack(pady=10)

        btn_del_sel = tk.Button(btn_frame, text=self.txt["btn_del_selected"], command=delete_selected, **self.btn_style)
        btn_del_sel.pack(side="left", padx=5)

        btn_del_all = tk.Button(btn_frame, text=self.txt["btn_clear_archive"], command=delete_all_archive, **self.btn_style, foreground="red")
        btn_del_all.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame, text=self.txt["btn_close"], command=arch_win.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="left", padx=5)

    #OKNO SZCZEGOLOW ARCHIWUM
    def archive_datails_window(self, exam_data, callback=None):
        hist_window = tk.Toplevel(self.root)

        info_frame = tk.Frame(hist_window)
        info_frame.pack(pady=10)

        lbl_subject = tk.Label(info_frame, text="", font=("Arial", 12, "bold"))
        lbl_subject.pack()
        lbl_date = tk.Label(info_frame, text="", font=("Arial", 12, "bold"))
        lbl_date.pack()



        def refresh_info():
            lbl_subject.config(text=f"{exam_data["subject"]} ({exam_data["title"]})")
            lbl_date.config(text=self.txt["msg_exam_date"].format(date=exam_data["date"]))
            hist_window.title(self.txt["win_archive_details_title"].format(subject=exam_data["subject"]))

        refresh_info()

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

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        def refresh_details():
            for item in tree.get_children():
                tree.delete(item)

            exam_topics = [t for t in self.data["topics"] if t["exam_id"] == exam_data["id"]]
            exam_topics.sort(key=lambda x: str(x.get("scheduled_date") or "9999-99-99"))

            for topic in exam_topics:
                status_text = self.txt["tag_done"] if topic["status"] == "done" else self.txt["tag_todo"]
                sched_date = topic.get("scheduled_date") if topic.get("scheduled_date") else "-"

                tree.insert("", "end", iid=topic["id"], values=(topic["name"], status_text, sched_date), tags=(topic["status"],))

        refresh_details()

        def toggle_status_local():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_topic"])
                return

            topic_id = selected[0]
            topic = next((t for t in self.data["topics"] if t["id"] == topic_id), None)

            if topic:
                if topic["status"] == "todo":
                    topic["status"] = "done"
                else:
                    topic["status"] = "todo"

                save(self.data)
                refresh_details()

        def edit_topic_local():
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_topic"])
                return

            topic_id = selected[0]
            topic = next((t for t in self.data["topics"] if t["id"] == topic_id), None)

            if topic:
                self.edit_topic_window(topic, callback=refresh_details)

        def edit_exam_local():
            def saved():
                refresh_details()
                refresh_info()
                if callback:
                    callback()

            self.edit_exam_window(exam_data, callback=saved)

        tree.bind("<Double-1>", lambda event: edit_topic_local())

        tk.Label(hist_window, text=self.txt["msg_double_click_edit"], font=("Arial", 12, "bold")).pack()

        btn_frame = tk.Frame(hist_window)
        btn_frame.pack(pady=10)

        btn_status = tk.Button(btn_frame, text=self.txt["btn_toggle_status"], command=toggle_status_local,**self.btn_style)
        btn_status.pack(side="left", padx=5)

        btn_edit = tk.Button(btn_frame, text=self.txt["btn_edit_exam"], command=edit_exam_local, **self.btn_style)
        btn_edit.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame, text=self.txt["btn_close"], command=hist_window.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="left", padx=5)



if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()
