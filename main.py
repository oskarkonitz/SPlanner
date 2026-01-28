import os
import sys
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
        self.current_lang = self.data["settings"].get("lang", "en")
        self.txt = load_language(self.current_lang)

        #  Konfiguracja okna
        self.root.title(self.txt["app_title"])
        # self.root.resizable(False, False)
        self.root.geometry("1200x650")

        # Uklad grid
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Menu gorne
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # menu plik
        file_menu = tk.Menu(self.menubar, tearoff=0)
        file_menu.add_command(label=self.txt["btn_clear_data"], command=self.menu_clear_data)
        file_menu.add_separator()
        file_menu.add_command(label=self.txt["btn_exit"], command=self.root.quit)
        self.menubar.add_cascade(label=self.txt["menu_file"], menu=file_menu)

        #menu narzedzia
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        tools_menu.add_command(label=self.txt["btn_add_exam"], command=self.sidebar_add)
        tools_menu.add_separator()
        tools_menu.add_command(label=self.txt["btn_refresh"], command=self.menu_refresh)
        tools_menu.add_command(label=self.txt["btn_gen_plan"], command=self.menu_gen_plan)
        tools_menu.add_separator()
        tools_menu.add_command(label=self.txt["win_archive_title"], command=self.sidebar_archive)
        self.menubar.add_cascade(label=self.txt["menu_tools"], menu=tools_menu)

        # menu ustawienia
        settings_menu = tk.Menu(self.menubar, tearoff=0)

        # --- Podmenu 1: Języki (Languages) ---
        lang_menu = tk.Menu(settings_menu, tearoff=0)

        # Zmienna trzymająca aktualny język
        self.selected_lang_var = tk.StringVar(value=self.current_lang)
        self.lang_map = {"English": "en", "Polski": "pl", "Deutsch": "de", "Español": "es"}

        for name, code in self.lang_map.items():
            lang_menu.add_radiobutton(
                label=name,
                value=code,
                variable=self.selected_lang_var,
                command=lambda c=code: self.change_language(c)
            )

        # Dodajemy podmenu Języki do menu Settings
        settings_menu.add_cascade(label=self.txt.get("lang_label", "Language"), menu=lang_menu)

        # --- Podmenu 2: Kolory (Colors) ---
        colors_menu = tk.Menu(settings_menu, tearoff=0)

        # Zmienna trzymająca aktualny motyw (domyślnie system)
        self.selected_theme_var = tk.StringVar(value="system")

        # Pusta funkcja, żeby nic się nie psuło przy klikaniu
        def dummy_theme_change():
            pass

        # Opcje kolorystyczne
        colors_menu.add_radiobutton(label=self.txt.get("theme_system", "System"), value="system", variable=self.selected_theme_var, command=dummy_theme_change)
        colors_menu.add_radiobutton(label=self.txt.get("theme_light", "Light"), value="light", variable=self.selected_theme_var, command=dummy_theme_change)
        colors_menu.add_radiobutton(label=self.txt.get("theme_dark", "Dark"), value="dark", variable=self.selected_theme_var, command=dummy_theme_change)

        # Dodajemy podmenu Kolory do menu Settings
        settings_menu.add_cascade(label=self.txt.get("menu_colors", "Colors"), menu=colors_menu)

        # --- Dodajemy główne menu Settings do paska ---
        self.menubar.add_cascade(label=self.txt.get("menu_settings", "Settings"), menu=settings_menu)

        # menu pomoc
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label=self.txt["btn_manual"], command=self.open_manual)
        self.menubar.add_cascade(label=self.txt["menu_help"], menu=help_menu)

        self.sidebar = tk.Frame(self.root, width=250)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        #  Tytuł aplikacji
        self.label_title = tk.Label(self.sidebar, text=self.txt["menu_app_title"], font=("Arial", 20, "bold"))
        self.label_title.pack(pady=(20, 10))

        #  Ramka statystyk (Dashboard)
        self.stats_frame = tk.Frame(self.sidebar)
        self.stats_frame.pack(fill="x", padx=10, pady=10, ipady=10)

        # Etykiety wewnątrz ramki
        self.lbl_next_exam = tk.Label(self.stats_frame, font=("Arial", 13, "bold"), wraplength=230, justify="center")
        self.lbl_next_exam.pack(pady=(2, 20))

        self.lbl_today = tk.Label(self.stats_frame, font=("Arial", 12, "bold"), wraplength=230, justify="center")
        self.lbl_today.pack(pady=2)

        self.lbl_progress = tk.Label(self.stats_frame, font=("Arial", 12, "bold"), wraplength=230, justify="center")
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
        # tk.Label(self.root, text=self.txt["menu_title"], font=("Arial", 14, "bold")).pack(pady=20, padx=60)

        btn_exit = tk.Button(self.sidebar, text=self.txt["btn_exit"], command=self.root.quit, **self.btn_style, activeforeground="red")
        btn_exit.pack(side="bottom", pady=30)

        # btn_start = tk.Button(self.root, text=self.txt["btn_run"], command=self.open_plan_window, **self.btn_style)
        # btn_start.pack(pady=10)
        self.middle_frame = tk.Frame(self.sidebar)
        self.middle_frame.pack(expand=True)

        # btn_add = tk.Button(self.middle_frame, text=self.txt["btn_add_exam"], command=self.sidebar_add, **self.btn_style)
        # btn_add.pack(pady=5)

        btn_status = tk.Button(self.middle_frame, text=self.txt["btn_toggle_status"], command=self.sidebar_toggle, **self.btn_style)
        btn_status.pack(pady=5)

        btn_edit = tk.Button(self.middle_frame, text=self.txt["btn_edit"], command=self.sidebar_edit, **self.btn_style)
        btn_edit.pack(pady=5)
        # btn_arch = tk.Button(self.sidebar, text=self.txt["btn_all_exams"], command=self.sidebar_archive, **self.btn_style)
        # btn_arch.pack(pady=5)
        # btn_man = tk.Button(self.sidebar, text=self.txt["btn_manual"], command=self.open_manual, **self.btn_style)
        # btn_man.pack(pady=10)


        #  Lista wyboru języka
        # self.setup_language_selector()

        #  Pierwsze obliczenie statystyk
        self.refresh_dashboard()

        self.plan_container = tk.Frame(self.root)
        self.plan_container.grid(row=0, column=1, sticky="nsew")

        self.plan_view = PlanWindow(parent=self.plan_container, txt=self.txt, data=self.data, btn_style=self.btn_style, dashboard_callback=self.refresh_dashboard)

        self.sidebar.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.middle_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.label_title.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.stats_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())

    def sidebar_add(self):
        self.plan_view.open_add_window()

    def sidebar_toggle(self):
        self.plan_view.toggle_status()

    def sidebar_edit(self):
        self.plan_view.open_edit()

    def sidebar_archive(self):
        self.plan_view.open_archive()

    def menu_gen_plan(self):
        self.plan_view.run_and_refresh()

    def menu_refresh(self):
        self.plan_view.refresh_table()

    def menu_clear_data(self):
        self.plan_view.clear_database()

    def change_language(self, new_code):
        # Jeśli język jest ten sam co był, nic nie rób
        if new_code == self.data["settings"].get("lang", "en"):
            return

        # Zapisz nowy język w bazie
        self.data["settings"]["lang"] = new_code
        save(self.data)

        # Zapytaj użytkownika czy zrestartować
        # Używamy askyesno: TAK = Restart, NIE = Później
        restart = messagebox.askyesno(self.txt["msg_info"], self.txt["msg_lang_changed"])

        if restart:
            # Magiczna komenda restartująca aplikację
            self.root.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

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
                standard_color = self.lbl_progress.cget("foreground")
                self.lbl_today.config(foreground=standard_color)
        else:
            self.lbl_today.config(text=self.txt["stats_no_today"], foreground="lightblue")

        # C. Najbliższy egzamin
        future_exams = [e for e in self.data["exams"] if date_format(e["date"]) >= today]
        future_exams.sort(key=lambda x: x["date"])

        if future_exams:
            nearest = future_exams[0]
            days = (date_format(nearest["date"]) - today).days

            same_day_exams = [e for e in future_exams if e["date"] == nearest["date"]]
            subjects_str = ",\n".join([e["subject"] for e in same_day_exams])

            color = "green"
            text = ""

            if days == 0:
                text = self.txt["stats_exam_today"].format(subject=subjects_str)
                color = "violet"
            elif days == 1:
                text = self.txt["stats_exam_tomorrow"].format(subject=subjects_str)
                color = "orange"
            else:
                text = self.txt["stats_exam_days"].format(days=days, subject=subjects_str)
                if days <= 5: color = "yellow"

            self.lbl_next_exam.config(text=text, foreground=color)
        else:
            self.lbl_next_exam.config(text=self.txt["stats_no_upcoming"], foreground="green")

    # Funkcja zawierająca selector języka i zmieniająca go po zmianie przez użytkownika
    # def setup_language_selector(self):
    #     bottom_frame = tk.Frame(self.sidebar)
    #     bottom_frame.pack(side="bottom", fill="x", padx=10, pady=10)
    #
    #     self.lang_map = {"English": "en", "Polski": "pl", "Deutsch": "de", "Español": "es"} #mapa jezykow do wyboru
    #     self.lang_rev = {v: k for k, v in self.lang_map.items()} #odwrocona mapa jezykow
    #
    #     self.combo_lang = ttk.Combobox(bottom_frame, values=list(self.lang_map.keys()), state="readonly", width=10)
    #     current_code = self.data["settings"].get("lang", "en") #pobranie aktualnego kodu z bazy
    #     self.combo_lang.set(self.lang_rev.get(current_code, "English")) #ustawienie combobox na aktualny kod
    #     self.combo_lang.pack(side="right")
    #
    #     # funkcja zmieniajaca jezyk w bazie danych
    #     def language_change(event):
    #         selected_name = self.combo_lang.get()
    #         new_code = self.lang_map[selected_name]
    #         if new_code != self.data["settings"].get("lang", "en"):
    #             self.data["settings"]["lang"] = new_code
    #             save(self.data)
    #             messagebox.showinfo(self.txt["msg_info"], self.txt["msg_lang_changed"])
    #
    #     # wykrycie zmiany przez uzytkownika
    #     self.combo_lang.bind("<<ComboboxSelected>>", language_change)

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