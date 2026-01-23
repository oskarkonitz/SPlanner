import tkinter as tk
from tkinter import messagebox, ttk
from datetime import date
from core.storage import load, save, load_language
from core.planner import date_format
from gui.windows.plan import PlanWindow
from gui.windows.manual import ManualWindow


class GUI:
    def __init__(self, root):
        self.root = root

        #  Ładowanie danych
        self.data = load()
        current_lang_code = self.data["settings"].get("lang", "en")
        self.txt = load_language(current_lang_code)

        #  Konfiguracja okna
        self.root.title(self.txt["app_title"])
        self.root.resizable(False, False)

        #  Tytuł aplikacji
        self.label_title = tk.Label(self.root, text=self.txt["menu_app_title"], font=("Arial", 20, "bold"))
        self.label_title.pack(pady=(20, 10))

        #  Ramka statystyk (Dashboard)
        self.stats_frame = tk.Frame(self.root)
        self.stats_frame.pack(fill="x", padx=40, pady=10, ipady=10)

        # Etykiety wewnątrz ramki
        self.lbl_next_exam = tk.Label(self.stats_frame, font=("Arial", 13, "bold"))
        self.lbl_next_exam.pack(pady=2)

        self.lbl_today = tk.Label(self.stats_frame, font=("Arial", 12, "bold"))
        self.lbl_today.pack(pady=2)

        self.lbl_progress = tk.Label(self.stats_frame, font=("Arial", 12, "bold"))
        self.lbl_progress.pack(pady=5)

        #  Styl przycisków
        self.btn_style = {
            "font": ("Arial", 11, "bold"),
            "cursor": "hand2",
            "height": 2,
            "width": 18,
            "relief": "flat",
            "bg": "#e1e1e1"
        }

        #  Menu Główne
        tk.Label(self.root, text=self.txt["menu_title"], font=("Arial", 14, "bold")).pack(pady=20, padx=60)

        btn_start = tk.Button(self.root, text=self.txt["btn_run"], command=self.open_plan_window, **self.btn_style)
        btn_start.pack(pady=10)
        btn_man = tk.Button(self.root, text=self.txt["btn_manual"], command=self.open_manual, **self.btn_style)
        btn_man.pack(pady=10)
        btn_exit = tk.Button(self.root, text=self.txt["btn_exit"], command=self.root.quit, **self.btn_style, activeforeground="red")
        btn_exit.pack(pady=40)

        #  Lista wyboru języka
        self.setup_language_selector()

        #  Pierwsze obliczenie statystyk
        self.refresh_dashboard()

    # Funkcja odświeżająca statystyki na ekranie początkowym
    def refresh_dashboard(self):
        today = date.today()

        # A. Postęp ogólny
        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= today}
        active_topics = [t for t in self.data["topics"] if t["exam_id"] in active_exams_ids]

        total_topics = len(active_topics)
        done_topics = len([t for t in active_topics if t["status"] == "done"])
        progress = int((done_topics / total_topics) * 100) if total_topics > 0 else 0

        self.lbl_progress.config(text=self.txt["stats_total_progress"].format(done=done_topics, total=total_topics, progress=progress))

        # B. Postęp dzienny
        today_all = [t for t in self.data["topics"] if str(t.get("scheduled_date")) == str(today)]
        t_total = len(today_all)
        t_done = len([t for t in today_all if t["status"] == "done"])

        if t_total > 0:
            t_prog = int((t_done / t_total) * 100)
            self.lbl_today.config(text=self.txt["stats_progress_today"].format(done=t_done, total=t_total, prog=t_prog))
            if t_prog == 100:
                self.lbl_today.config(foreground="green")
        else:
            self.lbl_today.config(text=self.txt["stats_no_today"], foreground="lightblue")

        # C. Najbliższy egzamin
        future_exams = [e for e in self.data["exams"] if date_format(e["date"]) >= today]
        future_exams.sort(key=lambda x: x["date"])

        if future_exams:
            nearest = future_exams[0]
            days = (date_format(nearest["date"]) - today).days
            color = "green"
            text = ""

            if days == 0:
                text = self.txt["stats_exam_today"].format(subject=nearest["subject"])
                color = "violet"
            elif days == 1:
                text = self.txt["stats_exam_tomorrow"].format(subject=nearest["subject"])
                color = "orange"
            else:
                text = self.txt["stats_exam_days"].format(days=days, subject=nearest["subject"])
                if days <= 5: color = "yellow"

            self.lbl_next_exam.config(text=text, foreground=color)
        else:
            self.lbl_next_exam.config(text=self.txt["stats_no_upcoming"], foreground="green")

    # Funkcja zawierająca selector języka i zmieniająca go po zmianie przez użytkownika
    def setup_language_selector(self):
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        self.lang_map = {"English": "en", "Polski": "pl", "Deutsch": "de", "Español": "es"} #mapa jezykow do wyboru
        self.lang_rev = {v: k for k, v in self.lang_map.items()} #odwrocona mapa jezykow

        self.combo_lang = ttk.Combobox(bottom_frame, values=list(self.lang_map.keys()), state="readonly", width=10)
        current_code = self.data["settings"].get("lang", "en") #pobranie aktualnego kodu z bazy
        self.combo_lang.set(self.lang_rev.get(current_code, "English")) #ustawienie combobox na aktualny kod
        self.combo_lang.pack(side="right")

        # funkcja zmieniajaca jezyk w bazie danych
        def language_change(event):
            selected_name = self.combo_lang.get()
            new_code = self.lang_map[selected_name]
            if new_code != self.data["settings"].get("lang", "en"):
                self.data["settings"]["lang"] = new_code
                save(self.data)
                messagebox.showinfo(self.txt["msg_info"], self.txt["msg_lang_changed"])

        # wykrycie zmiany przez uzytkownika
        self.combo_lang.bind("<<ComboboxSelected>>", language_change)

    #   OBSLUGA PRZYCISKOW NA EKRANIE POWITALNYM

    # uruchomienie okna z instrukcja
    def open_manual(self):
        ManualWindow(self.root, self.txt, self.btn_style)

    # uruchomienie glownego okna aplikacji
    def open_plan_window(self):
        # dashboard_callback aby po zmianach w planie (np wykonano jakies zadanie) okno powitalne odswiezalo statystyki
        PlanWindow(self.root, self.txt, self.data, self.btn_style, dashboard_callback=self.refresh_dashboard)

# uruchomienie aplikacji
if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()