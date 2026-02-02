import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date, datetime
from datetime import date
from core.storage import load, save, load_language
from core.planner import date_format
from gui.windows.plan import PlanWindow
from gui.windows.manual import ManualWindow
from gui.theme_manager import apply_theme, THEMES
from gui.windows.blocked_days import BlockedDaysWindow
from gui.effects import ConfettiEffect, FireworksEffect
from gui.windows.timer import TimerWindow
from gui.windows.achievements import AchievementManager
import threading
from core.updater import check_for_updates
from gui.windows.plan import ToolsDrawer

VERSION = "1.1.0"

class GUI:
    def __init__(self, root):
        self.root = root

        #  Ładowanie danych
        self.data = load()

        # --- MIGRACJA DANYCH DO SYSTEMU GLOBALNEGO (PERSISTENT STATS) ---
        if "global_stats" not in self.data:
            # Jeśli to pierwsze uruchomienie po aktualizacji, zliczamy to co jest teraz
            # żeby użytkownik nie zaczynał od zera, jeśli ma już bazę.
            existing_notes = sum(1 for t in self.data.get("topics", []) if t.get("note", "").strip())
            existing_notes += sum(1 for e in self.data.get("exams", []) if e.get("note", "").strip())

            existing_done = sum(1 for t in self.data.get("topics", []) if t["status"] == "done")
            existing_exams = len(self.data.get("exams", []))
            existing_blocked = len(self.data.get("blocked_dates", []))

            # Pobieramy pomodoro ze starego miejsca (stats -> pomodoro_count)
            existing_pomodoro = self.data.get("stats", {}).get("pomodoro_count", 0)

            self.data["global_stats"] = {
                "topics_done": existing_done,
                "notes_added": existing_notes,
                "exams_added": existing_exams,
                "days_off": existing_blocked,
                "pomodoro_sessions": existing_pomodoro,
                "activity_started": False  # Flaga do Clean Sheet (musi coś zrobić, żeby dostać)
            }
            # Jeśli użytkownik ma już jakieś zrobione zadania, uznajemy, że activity_started = True
            if existing_done > 0:
                self.data["global_stats"]["activity_started"] = True

            save(self.data)
        # ---------------------------------------------------------------

        self.status_btn_mode = "default"
        self.edit_btn_mode = "default"
        self.current_theme = self.data["settings"].get("theme", "light")
        self.current_lang = self.data["settings"].get("lang", "en")
        self.txt = load_language(self.current_lang)

        self.ach_manager = AchievementManager(self.root, self.txt, self.data)
        # Sprawdzamy cicho na starcie
        self.ach_manager.check_all(silent=True)

        #  Konfiguracja okna
        self.root.title(self.txt["app_title"])
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

        # menu narzedzia
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        tools_menu.add_command(label=self.txt["btn_refresh"], command=self.menu_refresh)
        tools_menu.add_separator()
        tools_menu.add_command(label=self.txt["btn_add_exam"], command=self.sidebar_add)
        tools_menu.add_separator()
        tools_menu.add_command(label=self.txt.get("btn_gen_full", "Generate (Full)"), command=self.menu_gen_plan)
        tools_menu.add_command(label=self.txt.get("btn_gen_new", "Plan (Missing)"), command=self.menu_gen_plan_new)
        tools_menu.add_separator()
        tools_menu.add_command(label=self.txt.get("menu_days_off", "Days Off"), command=self.open_blocked_days)
        tools_menu.add_command(label=self.txt["win_archive_title"], command=self.sidebar_archive)
        self.menubar.add_cascade(label=self.txt["menu_tools"], menu=tools_menu)

        # menu dodatki
        addons_menu = tk.Menu(self.menubar, tearoff=0)
        addons_menu.add_command(label=self.txt["menu_timer"], command=self.open_timer)
        addons_menu.add_separator()
        addons_menu.add_command(label=self.txt.get("win_achievements", "Osiągnięcia"),
                                command=self.open_achievements)
        self.menubar.add_cascade(label=self.txt["menu_addons"], menu=addons_menu)

        # menu ustawienia
        settings_menu = tk.Menu(self.menubar, tearoff=0)

        # --- NOWE MENU: PRZEŁĄCZANIE EGZAMINU ---
        switch_menu = tk.Menu(settings_menu, tearoff=0)
        # Pobieramy zapisaną godzinę (domyślnie 24 = północ)
        current_switch = self.data["settings"].get("next_exam_switch_hour", 24)
        self.switch_hour_var = tk.IntVar(value=current_switch)

        # Opcje godzinowe (możesz dodać własne)
        hours_options = [12, 14, 16, 18, 20, 22]

        for h in hours_options:
            label = f"{h}{self.txt.get('switch_hour_suffix', ':00')}"
            switch_menu.add_radiobutton(label=label, value=h, variable=self.switch_hour_var,
                                        command=lambda h=h: self.set_switch_hour(h))

        # Opcja domyślna (Północ)
        switch_menu.add_separator()
        switch_menu.add_radiobutton(label=self.txt.get("switch_midnight", "Midnight"), value=24,
                                    variable=self.switch_hour_var,
                                    command=lambda: self.set_switch_hour(24))

        settings_menu.add_cascade(label=self.txt.get("menu_switch_time", "Switch Time"), menu=switch_menu)

        # Języki
        lang_menu = tk.Menu(settings_menu, tearoff=0)
        self.selected_lang_var = tk.StringVar(value=self.current_lang)
        self.lang_map = {"English": "en", "Polski": "pl", "Deutsch": "de", "Español": "es"}

        for name, code in self.lang_map.items():
            lang_menu.add_radiobutton(
                label=name,
                value=code,
                variable=self.selected_lang_var,
                command=lambda c=code: self.change_language(c)
            )
        settings_menu.add_cascade(label=self.txt.get("lang_label", "Language"), menu=lang_menu)

        # Kolory
        colors_menu = tk.Menu(settings_menu, tearoff=0)
        self.selected_theme_var = tk.StringVar(value=self.current_theme)

        colors_menu.add_radiobutton(label=self.txt.get("theme_light", "Light"), value="light",
                                    variable=self.selected_theme_var, command=lambda: self.change_theme("light"))
        colors_menu.add_radiobutton(label=self.txt.get("theme_dark", "Dark"), value="dark",
                                    variable=self.selected_theme_var, command=lambda: self.change_theme("dark"))

        settings_menu.add_cascade(label=self.txt.get("menu_colors", "Colors"), menu=colors_menu)

        settings_menu.add_separator()
        settings_menu.add_command(
            label=self.txt.get("menu_check_updates", "Check for updates"),
            command=lambda: check_for_updates(self.txt, silent=False)
        )

        self.menubar.add_cascade(label=self.txt.get("menu_settings", "Settings"), menu=settings_menu)

        # menu pomoc
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label=self.txt["btn_manual"], command=self.open_manual)
        self.menubar.add_cascade(label=self.txt["menu_help"], menu=help_menu)

        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0, fg_color="transparent")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        #  Tytuł aplikacji
        self.label_title = tk.Label(self.sidebar, text=self.txt["menu_app_title"], font=("Arial", 20, "bold"),
                                    wraplength=230, justify="center")
        self.label_title.pack(pady=(20, 10))

        #  Ramka statystyk (Dashboard)
        self.stats_frame = tk.Frame(self.sidebar)
        self.stats_frame.pack(fill="x", padx=10, pady=10, ipady=10)

        # 1. Najbliższy egzamin
        self.lbl_next_exam = ctk.CTkLabel(self.stats_frame, text="", font=("Arial", 14, "bold"), wraplength=230)
        self.lbl_next_exam.pack(pady=(10, 20))

        # 2. Postęp DZIŚ
        self.lbl_today = ctk.CTkLabel(self.stats_frame, text="", font=("Arial", 12, "bold"), wraplength=230,
                                      justify="center")
        self.lbl_today.pack(pady=(5, 2))

        self.bar_today = ctk.CTkProgressBar(self.stats_frame, width=180, height=6, corner_radius=5)
        self.bar_today.set(0)
        self.bar_today.configure(progress_color="#3498db")
        self.bar_today.pack(pady=(8, 15))

        # 3. Postęp CAŁKOWITY
        self.lbl_progress = ctk.CTkLabel(self.stats_frame, text="", font=("Arial", 12, "bold"), wraplength=230,
                                         justify="center")
        self.lbl_progress.pack(pady=(5, 2))

        self.bar_total = ctk.CTkProgressBar(self.stats_frame, width=180, height=6, corner_radius=5)
        self.bar_total.set(0)
        self.bar_total.configure(progress_color="#3498db")
        self.bar_total.pack(pady=(8, 10))

        #  Styl przycisków
        self.btn_style = {
            "font": ("Arial", 13, "bold"),
            "height": 32,
            "corner_radius": 20,
            "fg_color": "#3a3a3a",
            "text_color": "white",
            "hover_color": "#454545",  # <--- Dodano brakujący klucz (domyślny ciemny hover)
            "border_color": "#3a3a3a",  # <--- Dodano brakujący klucz
            "border_width": 0  # <--- Dodano brakujący klucz
        }

        self.btn_exit = ctk.CTkButton(self.sidebar, text=self.txt["btn_exit"], command=self.root.quit, **self.btn_style)
        self.btn_exit.pack(side="bottom", pady=30)

        def on_enter_exit(event):
            self.btn_exit.configure(
                border_color="#e74c3c",
                text_color="#e74c3c",
                fg_color="transparent"
            )

        def on_leave_exit(event):
            self.btn_exit.configure(
                border_color=self.btn_style["border_color"],
                text_color=self.btn_style["text_color"],
                fg_color=self.btn_style["fg_color"]
            )

        self.btn_exit.bind("<Enter>", on_enter_exit)
        self.btn_exit.bind("<Leave>", on_leave_exit)

        # --- ZMIANA: Tę sekcję wklej ZAMIAST starego kodu przycisków w __init__ ---

        self.middle_frame = tk.Frame(self.sidebar)
        self.middle_frame.pack(expand=True, fill="x", padx=15)

        # Definicja nowych przycisków dynamicznych
        self.btn_1 = ctk.CTkButton(self.middle_frame, text="", **self.btn_style)
        self.btn_1.pack(pady=5, fill="x")

        self.btn_2 = ctk.CTkButton(self.middle_frame, text="", **self.btn_style)
        self.btn_2.pack(pady=5, fill="x")

        self.btn_3 = ctk.CTkButton(self.middle_frame, text="", **self.btn_style)
        self.btn_3.pack(pady=5, fill="x")

        # Kontener na widok planu
        self.plan_container = ctk.CTkFrame(self.root, fg_color="transparent", corner_radius=0)
        self.plan_container.grid(row=0, column=1, sticky="nsew")

        # --- WAŻNA POPRAWKA: selection_callback wskazuje na update_sidebar_buttons ---
        self.plan_view = PlanWindow(parent=self.plan_container, txt=self.txt, data=self.data, btn_style=self.btn_style,
                                    dashboard_callback=self.refresh_dashboard,
                                    selection_callback=self.update_sidebar_buttons)

        # --- NOWOŚĆ: WYMUSZAMY ODŚWIEŻENIE PRZYCISKÓW NA STARCIE ---
        # Dzięki temu nie będą szarymi paskami, tylko od razu pokażą "Add Exam", "Archive" itd.
        self.update_sidebar_buttons("idle", "idle", "idle")

        # Odznaczanie po kliknięciu w tło
        self.sidebar.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.middle_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.label_title.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.stats_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())

        self.effect_confetti = ConfettiEffect(self.sidebar)
        self.effect_fireworks = FireworksEffect(self.sidebar)

        self.celebration_shown = False

        # Inicjalizacja szufladki narzędziowej
        callbacks = {
            "timer": self.open_timer,
            "achievements": self.open_achievements,
            "days_off": self.open_blocked_days,
            "gen_full": self.menu_gen_plan,
            "gen_new": self.menu_gen_plan_new
        }
        self.tools_drawer = ToolsDrawer(self.root, self.txt, self.btn_style, callbacks)

        # Aplikowanie motywu i start
        apply_theme(self, self.current_theme)
        self.refresh_dashboard()

        # --- AUTO-UPDATE ---
        threading.Thread(target=lambda: check_for_updates(self.txt, silent=True), daemon=True).start()

    def sidebar_add(self):
        self.plan_view.open_add_window()

    def sidebar_toggle(self):
        self.plan_view.toggle_status()

    def sidebar_edit(self):
        self.plan_view.open_edit()

    def sidebar_archive(self):
        self.plan_view.open_archive()

    def menu_gen_plan(self):
        self.plan_view.run_and_refresh(only_unscheduled=False)

    def menu_gen_plan_new(self):
        self.plan_view.run_and_refresh(only_unscheduled=True)

    def menu_refresh(self):
        self.plan_view.refresh_table()

    def menu_clear_data(self):
        # Pobieramy potwierdzenie od użytkownika
        if messagebox.askyesno(self.txt.get("msg_confirm", "Confirm"), self.txt.get("msg_clear_confirm", "Clear all data?")):
            # 1. Resetowanie głównych danych planera
            self.data["exams"] = []
            self.data["topics"] = []
            self.data["notes"] = {}
            self.data["blocked_dates"] = []

            # 2. Resetowanie Osiągnięć i Statystyk globalnych
            self.data["achievements"] = []
            self.data["global_stats"] = {
                "topics_done": 0,
                "notes_added": 0,
                "exams_added": 0,
                "days_off": 0,
                "pomodoro_sessions": 0,
                "activity_started": False,
                "had_overdue": False
            }

            # 3. Zapisanie pustych struktur do pliku
            save(self.data)

            # 4. Synchronizacja i odświeżenie widoków
            self.plan_view.data = self.data  # Ważne: aktualizacja słownika w PlanWindow
            self.plan_view.refresh_table()
            self.refresh_dashboard()

            # 5. Reset managera osiągnięć (żeby wyczyścić jego wewnętrzną kolejkę)
            from gui.windows.achievements import AchievementManager
            self.ach_manager = AchievementManager(self.root, self.txt, self.data)

            messagebox.showinfo(self.txt.get("msg_info", "Info"), self.txt.get("msg_data_cleared", "Data cleared!"))

    def change_language(self, new_code):
        if new_code == self.data["settings"].get("lang", "en"):
            return
        self.data["settings"]["lang"] = new_code
        save(self.data)
        restart = messagebox.askyesno(self.txt["msg_info"], self.txt["msg_lang_changed"])
        if restart:
            self.root.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

    def set_switch_hour(self, hour):
        self.data["settings"]["next_exam_switch_hour"] = hour
        save(self.data)
        # Odśwież dashboard natychmiast, żeby zobaczyć efekt
        self.refresh_dashboard()

    def change_theme(self, theme_name):
        self.data["settings"]["theme"] = theme_name
        save(self.data)
        self.current_theme = theme_name
        apply_theme(self, theme_name)

    def open_blocked_days(self):
        # Przekazujemy self.refresh_dashboard jako refresh_callback
        BlockedDaysWindow(
            self.root,
            self.txt,
            self.data,
            self.btn_style,
            callback=self.menu_gen_plan,
            refresh_callback=self.refresh_dashboard # <--- TO NAPRAWIA PROBLEM
        )

    def update_sidebar_buttons(self, s1, s2, s3):
        # 1. RESET UI
        self.btn_1.pack_forget()
        self.btn_2.pack_forget()
        self.btn_3.pack_forget()

        def config_btn(btn, mode):
            if mode == "hidden" or mode == "disabled":
                return False

            # Reset do stylu bazowego
            current_text_col = self.btn_style.get("text_color", "white")
            current_hover = self.btn_style.get("hover_color", "#454545")

            # --- DEFINICJE KOLORÓW ---
            COL_GREEN = "#00b800"
            COL_BLUE = "#3399ff"
            COL_RED = "#e74c3c"
            COL_ORANGE = "#e67e22"

            text = "Button"
            cmd = None
            color = None

            # --- MAPOWANIE AKCJI ---
            if mode == "idle":
                pass

            # PRZYCISKI MENU
            elif mode == "add":
                text = self.txt["btn_add_exam"]
                cmd = self.sidebar_add
            elif mode == "archive":
                text = self.txt["win_archive_title"]
                cmd = self.sidebar_archive
            elif mode == "tools":
                text = self.txt.get("btn_tools", "Tools")
                cmd = self.toggle_tools_drawer

            # PRZYCISKI AKCJI
            elif mode == "complete":
                text = self.txt.get("tag_done", "Done")
                cmd = self.plan_view.toggle_status
                color = COL_GREEN

            elif mode == "restore":
                text = self.txt.get("btn_restore", "Restore")
                cmd = self.plan_view.restore_status

                # --- ZMIANA: Biały w Dark Mode, Szary w Light Mode ---
                if self.current_theme == "dark":
                    color = "#ffffff"
                else:
                    color = "gray"

            elif mode.startswith("edit"):
                text = self.txt["btn_edit"]
                cmd = self.sidebar_edit
                color = COL_BLUE

            elif mode == "delete":
                text = self.txt["btn_delete"]
                cmd = self.plan_view.delete_selected_item
                color = COL_RED

            elif mode == "move_today":
                text = self.txt.get("btn_move_today", "To Today")
                cmd = self.plan_view.move_selected_to_today
                color = COL_ORANGE

            # --- ZMIANA: Ujednolicenie koloru czerwonego dla Block i Block & Gen ---
            elif mode == "block":
                text = self.txt.get("btn_block", "Block")
                cmd = lambda: self.plan_view.toggle_status(generate=False)
                color = COL_RED
            elif mode == "unblock":
                text = self.txt.get("btn_unblock", "Unblock")
                cmd = lambda: self.plan_view.toggle_status(generate=False)
                color = COL_GREEN
            elif mode == "block_gen":
                text = self.txt.get("btn_block_gen", "Block & Gen.")
                cmd = lambda: self.plan_view.toggle_status(generate=True)
                color = COL_RED
            elif mode == "unblock_gen":
                text = self.txt.get("btn_unblock_gen", "Unblock & Gen.")
                cmd = lambda: self.plan_view.toggle_status(generate=True)
                color = COL_GREEN

            # --- APLIKOWANIE STYLU ---
            btn.configure(text=text, command=cmd)

            if color:
                # STYL "OUTLINE"
                btn.configure(
                    fg_color="transparent",
                    border_color=color,
                    text_color=color,
                    border_width=1.2,
                    hover_color=current_hover
                )
            else:
                # STYL "SOLID"
                btn.configure(
                    fg_color=self.btn_style["fg_color"],
                    text_color=current_text_col,
                    border_color=self.btn_style.get("border_color", "gray"),
                    border_width=1,
                    hover_color=current_hover
                )

            return True

        if s1 == "idle":
            s1, s2, s3 = "add", "archive", "tools"

        show_1 = config_btn(self.btn_1, s1)
        show_2 = config_btn(self.btn_2, s2)
        show_3 = config_btn(self.btn_3, s3)

        if show_1: self.btn_1.pack(pady=5, fill="x")
        if show_2: self.btn_2.pack(pady=5, fill="x")
        if show_3: self.btn_3.pack(pady=5, fill="x")

        self.middle_frame.update_idletasks()

    def toggle_tools_drawer(self):
        if self.tools_drawer.is_open:
            self.tools_drawer.close_panel()
        else:
            self.tools_drawer.open_panel()

    def open_achievements(self):
        from gui.windows.achievements import AchievementsWindow
        AchievementsWindow(self.root, self.txt, self.data, self.btn_style)

    def open_timer(self):
        TimerWindow(self.root, self.txt, self.btn_style, self.data, callback=self.refresh_dashboard)

    def animate_bar(self, bar, target_value):
        current_value = bar.get()
        diff = target_value - current_value

        if abs(diff) < 0.005:
            bar.set(target_value)
            return

        steps = 25
        duration = 10
        step_size = diff / steps

        def _step(iteration):
            new_val = current_value + (step_size * (iteration + 1))
            bar.set(new_val)
            if iteration < steps - 1:
                self.root.after(duration, _step, iteration + 1)
            else:
                bar.set(target_value)

        _step(0)

    def refresh_dashboard(self):
        today = date.today()
        current_colors = THEMES.get(self.current_theme, THEMES["light"])
        default_text = current_colors["fg_text"]

        # A. Postęp Całkowity
        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= today}
        active_topics = [t for t in self.data["topics"] if t["exam_id"] in active_exams_ids]
        total = len(active_topics)
        done = len([t for t in active_topics if t["status"] == "done"])

        prog_val = 0.0
        prog_percent = 0
        if total > 0:
            prog_val = done / total
            prog_percent = int(prog_val * 100)

        self.lbl_progress.configure(
            text=self.txt["stats_total_progress"].format(done=done, total=total, progress=prog_percent))
        self.animate_bar(self.bar_total, prog_val)

        # B. Postęp Dziś
        today_all = [t for t in self.data["topics"] if str(t.get("scheduled_date")) == str(today)]
        t_tot = len(today_all)
        t_don = len([t for t in today_all if t["status"] == "done"])

        if t_tot > 0:
            p_day_val = t_don / t_tot
            p_day_perc = int(p_day_val * 100)

            self.lbl_today.configure(
                text=self.txt["stats_progress_today"].format(done=t_don, total=t_tot, prog=p_day_perc))

            if p_day_perc == 100:
                self.lbl_today.configure(text_color="#00b800")
                self.bar_today.configure(progress_color="#2ecc71")

                if not self.celebration_shown:
                    import random
                    raw_msg = self.txt.get("msg_all_done", ["Good Job!"])
                    msg = random.choice(raw_msg) if isinstance(raw_msg, list) else raw_msg

                    effect_type = random.choice(["confetti", "fireworks"])
                    if effect_type == "confetti":
                        self.effect_confetti.start(text=msg)
                    else:
                        self.effect_fireworks.start(text=msg)

                    self.celebration_shown = True
            else:
                self.lbl_today.configure(text_color=default_text)
                self.bar_today.configure(progress_color="#3498db")
                self.celebration_shown = False
            self.animate_bar(self.bar_today, p_day_val)
        else:
            self.lbl_today.configure(text=self.txt["stats_no_today"], text_color="#1f6aa5")
            self.bar_today.set(0)

        # C. Najbliższy egzamin
        # 1. Sprawdzamy ustawienia godziny
        switch_hour = self.data["settings"].get("next_exam_switch_hour", 24)
        now_hour = datetime.now().hour

        # 2. Decyzja: czy "dzisiaj" już minęło?
        # Jeśli aktualna godzina >= ustawionej (i nie jest to północ 24), to szukamy od JUTRA
        if switch_hour < 24 and now_hour >= switch_hour:
            # Szukamy egzaminów TYLKO w przyszłości (> today)
            future_exams = [e for e in self.data["exams"] if date_format(e["date"]) > today]
        else:
            # Standardowo: szukamy od dzisiaj włącznie (>= today)
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
                if days <= 5:
                    if self.current_theme == "light":
                        color = "#e6b800"
                    else:
                        color = "yellow"

            self.lbl_next_exam.configure(text=text, text_color=color)
        else:
            self.lbl_next_exam.configure(text=self.txt["stats_no_upcoming"], text_color="green")

        if hasattr(self, 'ach_manager'):
            self.ach_manager.check_all(silent=False)

    def open_manual(self):
        ManualWindow(self.root, self.txt, self.btn_style)

    def open_plan_window(self):
        PlanWindow(self.root, self.txt, self.data, self.btn_style, dashboard_callback=self.refresh_dashboard)


if __name__ == "__main__":
    root = ctk.CTk()
    app = GUI(root)
    root.mainloop()