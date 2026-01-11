import tkinter as tk
from tkinter import messagebox, ttk
from storage import load, save
from planner import plan, date_format
import uuid
from datetime import datetime, timedelta, date

class GUI:
    #FUNKCJA WYKONUJĄCA SIE NA POCZĄTKU
    def __init__(self, root):
        self.root = root
        self.root.title("Planer Nauki")
        #self.root.geometry("400x500")
        self.root.resizable(False, False)

        self.data = load()
        # print(f"Loaded exams: {len(self.data["exams"])}")

        # STYL PRZYCISKOW DLA CALEGO PROGRAMU
        self.btn_style = {
            "font": ("Arial", 11, "bold"),
            "cursor": "hand2",
            "height": 2,
            "width": 18,
            "relief": "flat",
            "bg": "#e1e1e1"
        }

        # PRZYCISKI W MENU GLOWNYM
        self.label_title = tk.Label(self.root, text="Wybierz opcje:", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=20, padx=60)
        self.btn_add = tk.Button(self.root, text="Dodaj Egzamin", command=self.add_window, **self.btn_style)
        self.btn_add.pack(pady=10)
        self.btn_plan = tk.Button(self.root, text="Generuj Plan", command=self.run_planner, **self.btn_style)
        self.btn_plan.pack(pady=10)
        self.btn_week = tk.Button(self.root, text="Pokaż Plan", command=self.show_plan, **self.btn_style)
        self.btn_week.pack(pady=10)
        self.btn_manual = tk.Button(self.root, text="Instrukcja Obsługi", command=self.manual, **self.btn_style)
        self.btn_manual.pack(pady=10)
        self.btn_exit = tk.Button(self.root, text="Wyjście", command=self.root.quit, **self.btn_style, activeforeground="red")
        self.btn_exit.pack(pady=40)

    #OKNO Z INSTRUKCJĄ
    def manual(self):
        man_win = tk.Toplevel(self.root)
        #man_win.geometry("450x500")
        man_win.title("Instrukcja Obsługi")

        frame = tk.Frame(man_win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, padx=10, pady=10)
        text.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=text.yview)

        text.tag_config("bold", font=("Arial", 20, "bold"))
        text.tag_config("normal", font=("Arial", 13))

        text.insert("end", "JAK KORZYSTAĆ Z PLANERA?\n\n", "bold")
        instrukcja = (
            "1. Dodawanie Egzaminu:\n"
            "Kliknij przycisk 'Dodaj Egzamin'. Wpisz nazwę przedmiotu, formę (np. kolokwium) "
            "oraz datę egzaminu. W dużym polu poniżej wpisz listę zagadnień do nauki "
            "- każde w nowej linii.\n\n"

            "2. Generowanie Planu:\n"
            "Po dodaniu egzaminów kliknij 'Generuj Plan'. Aplikacja automatycznie rozłoży "
            "Twoje zagadnienia na dni pomiędzy dniem dzisiejszym a datą egzaminu.\n\n"

            "3. Przeglądanie Planu:\n"
            "Kliknij 'Pokaż Plan', aby zobaczyć tabelę z zadaniami. Dni są posortowane chronologicznie."
            "Na czerwono zaznaczone są egzaminy a na zielono zadania wykonane.\n\n"
            
            "4. Praca z Planem:\n"
            "Jeśli podczas przeglądania planu dodasz nowy egzamin, to wystarczy wygenerować"
            "plan ponownie i odświeżyć Przeglądarke. Nie trzeba jej na nowo uruchamiać\n\n"

            "5. Zaznaczanie Postępów:\n"
            "W oknie planu zaznacz zadanie myszką i kliknij 'Zmień status'. "
            "Zadania zrobione zmienią kolor na zielony."
            "Jeśli jakiemuś zadaniu zmienisz status na zrobiony przez pomyłke to możesz to"
            "cofnąć ponownie zmieniając status.\n\n"

            "6. Resetowanie:\n"
            "Przycisk 'Wyczyść dane' usuwa trwale wszystko z bazy danych. Używaj ostrożnie, nie da się ich odzyskać!"
        )
        text.insert("end", instrukcja, "normal")
        text.configure(state="disabled")
        btn_close = tk.Button(man_win, text="Zamknij", command=man_win.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="bottom", pady=10)

    #FUNKCJA URUCHAMIAJĄCA PROGRAM PLANUJĄCY
    def run_planner(self):
        try:
            plan(self.data)
            save(self.data)
            messagebox.showinfo("Sukces", "Planowanie zakonczone")
        except Exception as e:
            messagebox.showerror("Błąd", f"Powod: {e}")

    #OKNO DO DODAWANIA NOWYCH EGZAMINOW I TEMATÓW
    def add_window(self):
        # FUNKCJA WEW. ZAPISUJACA DANE WPROWADZONE PRZEZ UZYTKOWNIKA
        def save_new_exam():
            subject = entry_subject.get()
            date_str = entry_date.get()
            title = entry_title.get()
            topics = text_topics.get("1.0", tk.END)

            if not subject or not date_str or not title:
                messagebox.showwarning("Błąd!", "Uzupelnij brakujace pola")
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
                    "scheduled_date": None
                })

            save(self.data)
            add_win.destroy()
            messagebox.showinfo("Sukces", f"Dodano egzamin i {len(topics_list)} tematów")

        add_win = tk.Toplevel(self.root)
        #add_win.geometry("460x400")
        add_win.resizable(False, False)
        add_win.title("Dodaj nowy egzamin")

        tk.Label(add_win, text="Przedmiot:").grid(row=0, column=0, pady=10, padx=10, sticky="e")
        entry_subject = tk.Entry(add_win, width=30)
        entry_subject.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(add_win, text="Forma:").grid(row=1, column=0, pady=10, padx=10, sticky="e")
        entry_title = tk.Entry(add_win, width=30)
        entry_title.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(add_win, text="Data (YYYY-MM-DD):").grid(row=2, column=0, pady=10, padx=10, sticky="e")
        entry_date = tk.Entry(add_win, width=30)
        entry_date.grid(row=2, column=1, padx=10, pady=10)
        tomorrow = datetime.now() + timedelta(days=1)
        entry_date.insert(0, tomorrow.strftime("%Y-%m-%d"))

        tk.Label(add_win, text="Tematy (jeden pod drugim):").grid(row=3, column=0, columnspan=2, pady=5)
        text_topics = tk.Text(add_win, width=40, height=10)
        text_topics.grid(row=4, column=0, columnspan=2, padx=10)

        btn_frame = tk.Frame(add_win)
        btn_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=20)

        btn_save = tk.Button(btn_frame, text="Zapisz", command=save_new_exam, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_exit = tk.Button(btn_frame, text="Anuluj", command=add_win.destroy, **self.btn_style, activeforeground="red")
        btn_exit.pack(side="left", padx=5)

    #FUNKCJE DO EDYCJI DANYCH

    #SPRAWDZENIE CO JEST ZAZNACZONE
    def edit_select(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "Najpierw zaznacz element, który chcesz edytować.")
            return

        item_id = selected_item[0]

        for exam in self.data["exams"]:
            if exam["id"] == item_id:
                self.edit_exam_window(exam)
                return

        for topic in self.data["topics"]:
            if topic["id"] == item_id:
                self.edit_topic_window(topic)
                return

        messagebox.showerror("Błąd", "Nie można edytować tego elementu.")

    #OKNO EDYCJI CALOSCI
    def edit_exam_window(self, exam_data):
        edit_win = tk.Toplevel(self.root)
        edit_win.resizable(False, False)
        edit_win.title(f"Edytuj: {exam_data["subject"]}")

        tk.Label(edit_win, text="Przedmiot:").grid(row=0, column=0, pady=5, padx=10, sticky="e")
        ent_subject = tk.Entry(edit_win, width=30)
        ent_subject.insert(0, exam_data["subject"])
        ent_subject.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(edit_win, text="Forma:").grid(row=1, column=0, pady=5, padx=10, sticky="e")
        ent_title = tk.Entry(edit_win, width=30)
        ent_title.insert(0, exam_data["title"])
        ent_title.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(edit_win, text="Data (YYYY-MM-DD):").grid(row=2, column=0, pady=5, padx=10, sticky="e")
        ent_date = tk.Entry(edit_win, width=30)
        ent_date.insert(0, exam_data["date"])
        ent_date.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(edit_win, text="Tematy (edycja listy):").grid(row=3, column=0, pady=5, columnspan=2)
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
                        "scheduled_date": None
                    })
                    topics_keep_ids.append(new_id)

            self.data["topics"] = [
                t for t in self.data["topics"]
                if t["exam_id"] != exam_data["id"] or t["id"] in topics_keep_ids
            ]

            save(self.data)
            edit_win.destroy()
            messagebox.showinfo("Sukces", "Dane zaktualizowane, kliknij Odśwież")

        def delete_exam():
            confirm = messagebox.askyesno("Uwaga", f"Czy na pewno chcesz usunąć '{exam_data["subject"]}'?")
            if confirm:
                self.data["topics"] = [t for t in self.data["topics"] if t["exam_id"] != exam_data["id"]]
                self.data["exams"] = [e for e in self.data["exams"] if e["id"] != exam_data["id"]]

                save(self.data)
                edit_win.destroy()
                messagebox.showinfo("Sukces", "Egzamin usunięty, odśwież aby zobaczyć zmiany.")

        btn_frame = tk.Frame(edit_win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        btn_save = tk.Button(btn_frame, text="Zapisz zmiany", command=save_changes, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_delete = tk.Button(btn_frame, text="Usuń", command=delete_exam, **self.btn_style, foreground="red")
        btn_delete.pack(side="left", padx=5)

        btn_cancel = tk.Button(btn_frame, text="Anuluj", command=edit_win.destroy, **self.btn_style, activeforeground="red")
        btn_cancel.pack(side="left", padx=5)

    #OKNO EDYCJI TEMATU
    def edit_topic_window(self, topic_data):
        topic_win = tk.Toplevel(self.root)
        topic_win.title(f"Edytuj: {topic_data["name"]}")
        topic_win.resizable(width=False, height=False)

        tk.Label(topic_win, text="Temat:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        ent_name = tk.Entry(topic_win, width=30)
        ent_name.insert(0, topic_data["name"])
        ent_name.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(topic_win, text="Data (YYYY-MM-DD):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        ent_date = tk.Entry(topic_win, width=30)
        if topic_data.get("scheduled_date"):
            ent_date.insert(0, topic_data["scheduled_date"])
        ent_date.grid(row=1, column=1, padx=10, pady=10)

        def save_changes():
            new_name = ent_name.get()
            new_date = ent_date.get()

            if not new_name:
                messagebox.showwarning("Błąd", "Temat musi mieć nazwę.")
                return

            topic_data["name"] = new_name

            if not new_date.strip():
                topic_data["scheduled_date"] = None
            else:
                topic_data["scheduled_date"] = new_date

            save(self.data)
            topic_win.destroy()
            messagebox.showinfo("Sukces", "Zaktualizowano temat, odśwież aby zobaczyć zmiany.")

        def delete_topic():
            confirm = messagebox.askyesno("Uwaga", "Czy na pewno chcesz usunąć to zadanie?")
            if confirm:
                self.data["topics"] = [t for t in self.data["topics"] if t["id"] != topic_data["id"]]
                save(self.data)
                topic_win.destroy()
                messagebox.showinfo("Sukces", "Usunięto zadanie.")

        btn_frame = tk.Frame(topic_win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        btn_save = tk.Button(btn_frame, text="Zapisz", command=save_changes, **self.btn_style)
        btn_save.pack(side="left", padx=5)

        btn_delete = tk.Button(btn_frame, text="Usuń", command=delete_topic, **self.btn_style, foreground="red")
        btn_delete.pack(side="left", padx=5)

        btn_cancel = tk.Button(btn_frame, text="Anuluj", command=topic_win.destroy, **self.btn_style, activeforeground="red")
        btn_cancel.pack(side="left", padx=5)

    #OKNO Z GOTOWYM PLANEM NAUKI
    def show_plan(self):
        week_win = tk.Toplevel(self.root)
        week_win.geometry("750x400")
        week_win.title("Plan Nauki")

        frame = tk.Frame(week_win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("data", "przedmiot", "temat")
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        tree.heading("data", text="Data")
        tree.column("data", width=100, anchor="center")
        tree.heading("przedmiot", text="Przedmiot")
        tree.column("przedmiot", width=150, anchor="w")
        tree.heading("temat", text="Temat | Zadanie | Forma Zaliczenia")
        tree.column("temat", width=300, anchor="w")

        tree.tag_configure("exam", foreground="red", font=("Arial", 13, "bold"))
        tree.tag_configure("done", foreground="green", font=("Arial", 12, "bold"))
        tree.tag_configure("date_header", font=("Arial", 13, "bold"))
        tree.tag_configure("todo", font=("Arial", 13, "bold"))

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        # FUNKCJA WEW. ODSWIEZAJACA WIDOK PLANU
        def refresh_table():
            for item in tree.get_children():
                tree.delete(item)

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
                        tree.insert("", "end", values=("", "", ""))
                        tree.insert("", "end", values=(day_str, "", ""), tags=("date_header",))
                        date_printed = True

                for exam in self.data["exams"]:
                    if exam["date"] == day_str:
                        print_date()
                        tree.insert("", "end", iid=exam["id"], values=("", exam["subject"], exam["title"]), tags=("exam",))
                for topic in self.data["topics"]:
                    if str(topic.get("scheduled_date")) == day_str:
                        subj_name = "Inne"
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
                messagebox.showinfo("Pomoc", "Najpierw zaznacz zadanie aby zmienić jego status")
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
                messagebox.showwarning("Błąd", "Nie można zmienić statusu tego elementu.")

        # FUNKCJA WEW. USUWAJACA DANE Z BAZY
        def clear_database():
            answer = messagebox.askyesno("UWAGA", "Czy na pewno chcesz usunąć WSZYSTKIE dane?\nTej operacji nie da się cofnąć!")
            if answer:
                self.data = {
                    "settings": {
                        "max_per_day": 2,
                        "max_same_subject_per_day": 1,
                    },
                    "exams": [],
                    "topics": []
                }
                save(self.data)
                refresh_table()
                messagebox.showinfo("Sukces", "Baza danych została zresetowana.")

        btn_frame1 = tk.Frame(week_win)
        btn_frame1.pack(pady=0)

        btn_frame2 = tk.Frame(week_win)
        btn_frame2.pack(pady=5)

        btn_refresh = tk.Button(btn_frame1, text="Odśwież", command=refresh_table, **self.btn_style)
        btn_refresh.pack(side="left", padx=5)

        btn_gen = tk.Button(btn_frame1, text="Generuj plan", command=self.run_planner, **self.btn_style)
        btn_gen.pack(side="left", padx=5)

        btn_toggle = tk.Button(btn_frame1, text="Zmień status", command=toggle_status, **self.btn_style)
        btn_toggle.pack(side="left", padx=5)

        btn_add = tk.Button(btn_frame1, text="Dodaj egzamin", command=self.add_window, **self.btn_style)
        btn_add.pack(side="left", padx=5)

        btn_edit = tk.Button(btn_frame2, text="Edytuj", command=lambda: self.edit_select(tree), **self.btn_style)
        btn_edit.pack(side="left", padx=5)

        btn_clear = tk.Button(btn_frame2, text="Wyczyść dane", command=clear_database, **self.btn_style, foreground="red")
        btn_clear.pack(side="left", padx=5)

        btn_close = tk.Button(btn_frame2, text="Zamknij", command=week_win.destroy, **self.btn_style, activeforeground="red")
        btn_close.pack(side="left", padx=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()
