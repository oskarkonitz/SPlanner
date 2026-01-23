import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date
from core.planner import date_format
from core.storage import save

class ArchiveWindow:
    def __init__(self, parent, txt, data, btn_style, edit_exam_func, edit_topic_func):
        self.txt = txt
        self.data = data
        self.btn_style = btn_style

        self.edit_exam_func = edit_exam_func
        self.edit_topic_func = edit_topic_func

        # USTAWIENIE OKNA
        self.win = tk.Toplevel(parent)
        self.win.title(self.txt["win_archive_title"])

        # LABELE
        tk.Label(self.win, text=self.txt["msg_archive_header"], font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(self.win, text=self.txt["msg_archive_sub"], font=("Arial", 12, "bold")).pack(pady=5)

        # RAMKA
        frame = tk.Frame(self.win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # TREE - LISTA Z DANYMI
        columns = ("data", "przedmiot", "forma", "status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("data", text=self.txt["col_date"])
        self.tree.column("data", width=100, anchor="center")
        self.tree.heading("przedmiot", text=self.txt["col_subject"])
        self.tree.column("przedmiot", width=180, anchor="w")
        self.tree.heading("forma", text=self.txt["col_form"])
        self.tree.column("forma", width=120, anchor="w")
        self.tree.heading("status", text=self.txt["col_status"])
        self.tree.column("status", width=150, anchor="center")

        # tagi dla kolorow
        self.tree.tag_configure("active", foreground="lightblue", font=("Arial", 12, "bold"))
        self.tree.tag_configure("past", foreground="gray", font=("Arial", 12, "bold"))

        # scroll
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # podwojne klikniecie otwiera szczegoły
        self.tree.bind("<Double-1>", self.on_double_click)

        # PRZYCISKI
        btn_frame = tk.Frame(self.win)
        btn_frame.pack(pady=10)

        btn_del_sel = tk.Button(btn_frame, text=self.txt["btn_del_selected"], command=self.delete_selected, **self.btn_style)
        btn_del_sel.pack(side="left", padx=5)

        btn_del_all = tk.Button(btn_frame, text=self.txt["btn_clear_archive"], command=self.delete_all_archive, **self.btn_style, foreground="red")
        btn_del_all.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame, text=self.txt["btn_close"], command=self.win.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="left", padx=5)

        # pierwsze odswiezenie listy
        self.refresh_list()

    # FUNKCJA ODSWIEZAJACA DANE W TABELCE
    def refresh_list(self):
        # wyczyszczenie tabelki
        for item in self.tree.get_children():
            self.tree.delete(item)

        # zebranie egzaminow i rozdzielenie ich na aktywne i przeszle
        today = date.today()
        all_exams = list(self.data["exams"])
        active_exams = []
        arch_exams = []

        for exam in all_exams:
            if date_format(exam["date"]) >= today:
                active_exams.append(exam)
            else:
                arch_exams.append(exam)

        # sortowanie - aktywne rosnaco a przeszle malejaco
        active_exams.sort(key=lambda x: x["date"])
        arch_exams.sort(key=lambda x: x["date"], reverse=True)

        # polaczenie dwoch tablic w jedna
        display_exams = active_exams + arch_exams

        # wstawianie elementow do tabelki z odpowiednimi tagami i datami
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

            # wstawienie do tabelki razem z id, ktore potem jest potrzebne aby program wiedzial, ktory egzamin mamy zaznaczony
            self.tree.insert("", "end", iid=exam["id"], values=(exam["date"], exam["subject"], exam["title"], status_txt), tags=(tag,))

    # FUNKCJA USUWAJACA ZAZNACZONY EGZAMIN
    def delete_selected(self):
        #ustalenie zaznaczonego egzaminu (mozliwe dzieki przypisaniu id)
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_del"])
            return

        exam_id = selection[0]

        # ustalenie danych o zaznaczonym egzaminie
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

        # wiadomosc potwierdzajaca czy na pewno usunac
        confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_perm"].format(type=type_of_exam, name=name))
        if confirm:
            # usuniecie
            self.data["topics"] = [t for t in self.data["topics"] if t["exam_id"] != exam_id]
            self.data["exams"] = [e for e in self.data["exams"] if e["id"] != exam_id]

            # zapisanie i odswiezenie
            save(self.data)
            self.refresh_list()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_archived_del"])

    # FUNKCJA USUWAJACA WSZYSTKIE PRZESZLE EGZAMINY
    def delete_all_archive(self):
        today = date.today()

        # sprawdzenie czy istnieja jakies przeszle egzaminy
        has_past = any(date_format(e["date"]) < today for e in self.data["exams"])
        if not has_past:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_no_archive"])
            return

        # pytanie czy na pewno
        confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_clear_archive"])
        if confirm:
            # tworzenie tablicy z id do usuniecia
            ids_to_remove = [e["id"] for e in self.data["exams"] if date_format(e["date"]) < today]

            # usuniecie egzaminow i tematow
            self.data["exams"] = [e for e in self.data["exams"] if date_format(e["date"]) >= today]
            self.data["topics"] = [t for t in self.data["topics"] if t["exam_id"] not in ids_to_remove]

            save(self.data)
            self.refresh_list()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_archive_cleared"])

    # FUNKCJA WYKONUJACA SIE NA PODWOJNE KLIKNIECIE I OTWIERAJACA DETAILS_WINDOW
    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        # ustalenie id egzaminu
        exam_id = selection[0]
        selected_exam = next((e for e in self.data["exams"] if e["id"] == exam_id), None)

        # otworzenie okna szegolow dla wybranego egzaminu
        if selected_exam:
            self.open_details_window(selected_exam)

    # FUNKCJA OTWIERAJACA OKNO SZCZEGOLOW DLA WYBRANEGO EGZAMINU
    def open_details_window(self, exam_data):
        hist_window = tk.Toplevel(self.win)

        info_frame = tk.Frame(hist_window)
        info_frame.pack(pady=10)

        lbl_subject = tk.Label(info_frame, text="", font=("Arial", 12, "bold"))
        lbl_subject.pack()
        lbl_date = tk.Label(info_frame, text="", font=("Arial", 12, "bold"))
        lbl_date.pack()

        # odswiezenie danych o egzaminie
        def refresh_info():
            lbl_subject.config(text=f"{exam_data['subject']} ({exam_data['title']})")
            lbl_date.config(text=self.txt["msg_exam_date"].format(date=exam_data['date']))
            hist_window.title(self.txt["win_archive_details_title"].format(subject=exam_data['subject']))

        refresh_info()

        # ustawienie widoku okna
        frame = tk.Frame(hist_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        #tabelka z tematami
        columns = ("temat", "status", "data_plan")
        tree = ttk.Treeview(frame, columns=columns, show="headings")

        tree.heading("temat", text=self.txt["col_topic"])
        tree.column("temat", width=250, anchor="w")
        tree.heading("status", text=self.txt["col_status"])
        tree.column("status", width=100, anchor="center")
        tree.heading("data_plan", text=self.txt["col_plan_date"])
        tree.column("data_plan", width=120, anchor="center")

        # tagi
        tree.tag_configure("done", foreground="green", font=("Arial", 12, "bold"))
        tree.tag_configure("todo", foreground="red", font=("Arial", 13, "bold"))

        #scroll
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        # odswiezenie szczegolow
        def refresh_details():
            for item in tree.get_children():
                tree.delete(item)

            # zebranie tematow ktore naleza do tego egzaminu
            exam_topics = [t for t in self.data["topics"] if t["exam_id"] == exam_data["id"]]
            # sortowanie rosnace a jesli brak daty to na koniec
            exam_topics.sort(key=lambda x: str(x.get("scheduled_date") or "9999-99-99"))

            # ustawienie danych to wsadzenia w tabelke
            for topic in exam_topics:
                status_text = self.txt["tag_done"] if topic["status"] == "done" else self.txt["tag_todo"]
                sched_date = topic.get("scheduled_date") if topic.get("scheduled_date") else "-"

                # wsadzenie danych do tabelki
                tree.insert("", "end", iid=topic["id"], values=(topic["name"], status_text, sched_date), tags=(topic["status"],))

        refresh_details()

        # funkcja zmieniaja status zadania i zapisujaca zmieny w bazie danych
        def toggle_status_local():
            # znalezienie zaznaczonego tematu
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_topic"])
                return

            topic_id = selected[0]
            topic = next((t for t in self.data["topics"] if t["id"] == topic_id), None)

            # zmiana statusu i zapisanie w bazie a na koniec odswiezenie widoku
            if topic:
                topic["status"] = "done" if topic["status"] == "todo" else "todo"
                save(self.data)
                refresh_details()

        # funkcja do edycji tematu
        def edit_topic_local():
            #znalezienie zaznaczonego elementu
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_topic"])
                return

            topic_id = selected[0]
            topic = next((t for t in self.data["topics"] if t["id"] == topic_id), None)

            # jesli to temat to uruchamia okno edycji dla tematu
            if topic:
                # wywoluje funkcje przekazana z plan
                self.edit_topic_func(topic, callback=refresh_details)

        def edit_exam_local():
            def saved():
                refresh_details()
                refresh_info()
                # odswiezenie listy archiwum
                self.refresh_list()

            # wywoluje funkcje przekazana z plan
            self.edit_exam_func(exam_data, callback=saved)

        # wykrywanie podwojnego klikniecia
        tree.bind("<Double-1>", lambda event: edit_topic_local())

        tk.Label(hist_window, text=self.txt["msg_double_click_edit"], font=("Arial", 12, "bold")).pack()

        # przyciski
        btn_frame = tk.Frame(hist_window)
        btn_frame.pack(pady=10)

        btn_status = tk.Button(btn_frame, text=self.txt["btn_toggle_status"], command=toggle_status_local, **self.btn_style)
        btn_status.pack(side="left", padx=5)

        btn_edit = tk.Button(btn_frame, text=self.txt["btn_edit_exam"], command=edit_exam_local, **self.btn_style)
        btn_edit.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame, text=self.txt["btn_close"], command=hist_window.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="left", padx=5)
