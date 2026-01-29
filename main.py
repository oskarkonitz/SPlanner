import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date
from core.storage import load, save, load_language
from core.planner import date_format
from gui.windows.plan import PlanWindow
from gui.windows.manual import ManualWindow
from gui.theme_manager import apply_theme, THEMES


class GUI:
    def __init__(self, root):
        self.root = root

        #  Ładowanie danych
        self.data = load()
        self.status_btn_mode = "default"
        self.edit_btn_mode = "default"
        self.current_theme = self.data["settings"].get("theme", "light")
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
        self.selected_theme_var = tk.StringVar(value=self.current_theme)

        # Opcje kolorystyczne
        colors_menu.add_radiobutton(label=self.txt.get("theme_light", "Light"), value="light", variable=self.selected_theme_var, command=lambda: self.change_theme("light"))
        colors_menu.add_radiobutton(label=self.txt.get("theme_dark", "Dark"), value="dark", variable=self.selected_theme_var, command=lambda: self.change_theme("dark"))

        # Dodajemy podmenu Kolory do menu Settings
        settings_menu.add_cascade(label=self.txt.get("menu_colors", "Colors"), menu=colors_menu)

        # --- Dodajemy główne menu Settings do paska ---
        self.menubar.add_cascade(label=self.txt.get("menu_settings", "Settings"), menu=settings_menu)

        # menu pomoc
        help_menu = tk.Menu(self.menubar, tearoff=0)
        help_menu.add_command(label=self.txt["btn_manual"], command=self.open_manual)
        self.menubar.add_cascade(label=self.txt["menu_help"], menu=help_menu)

        self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0, fg_color="transparent")
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.pack_propagate(False)

        #  Tytuł aplikacji
        self.label_title = tk.Label(self.sidebar, text=self.txt["menu_app_title"], font=("Arial", 20, "bold"), wraplength=230, justify="center")
        self.label_title.pack(pady=(20, 10))

        #  Ramka statystyk (Dashboard)
        self.stats_frame = tk.Frame(self.sidebar)
        self.stats_frame.pack(fill="x", padx=10, pady=10, ipady=10)

        # 1. Najbliższy egzamin
        self.lbl_next_exam = ctk.CTkLabel(self.stats_frame, text="", font=("Arial", 14, "bold"), wraplength=230)
        self.lbl_next_exam.pack(pady=(10, 20))

        # Etykiety wewnątrz ramki
        # 2. Postęp DZIŚ
        self.lbl_today = ctk.CTkLabel(self.stats_frame, text="", font=("Arial", 12, "bold"), wraplength=230, justify="center")
        self.lbl_today.pack(pady=(5, 2))

        # Pasek postępu DZIŚ
        self.bar_today = ctk.CTkProgressBar(self.stats_frame, width=180, height=6, corner_radius=5)
        self.bar_today.set(0)  # Startujemy od 0
        self.bar_today.configure(progress_color="#3498db")  # Zielony kolor paska
        self.bar_today.pack(pady=(8, 15))

        # 3. Postęp CAŁKOWITY
        self.lbl_progress = ctk.CTkLabel(self.stats_frame, text="", font=("Arial", 12, "bold"), wraplength=230, justify="center")
        self.lbl_progress.pack(pady=(5, 2))

        # Pasek postępu CAŁKOWITY
        self.bar_total = ctk.CTkProgressBar(self.stats_frame, width=180, height=6, corner_radius=5)
        self.bar_total.set(0)
        self.bar_total.configure(progress_color="#3498db")  # Niebieski kolor paska (dla odróżnienia)
        self.bar_total.pack(pady=(8, 10))

        #  Styl przycisków
        self.btn_style = {
            "font": ("Arial", 13, "bold"),
            "height": 32,
            "corner_radius": 20,
            "fg_color": "#3a3a3a",
            "text_color": "white"
        }

        #  Menu Główne
        # tk.Label(self.root, text=self.txt["menu_title"], font=("Arial", 14, "bold")).pack(pady=20, padx=60)

        self.btn_exit = ctk.CTkButton(self.sidebar, text=self.txt["btn_exit"], command=self.root.quit, **self.btn_style)
        self.btn_exit.pack(side="bottom", pady=30)

        # Funkcje obsługujące najechanie myszką
        def on_enter_exit(event):
            # Po najechaniu: Czerwona ramka i czerwony tekst
            self.btn_exit.configure(
                border_color="#e74c3c",
                text_color="#e74c3c",
                fg_color="transparent"  # Lub usuń tę linię, jeśli wolisz, by przycisk nie robił się przezroczysty
            )

        def on_leave_exit(event):
            # Po zjechaniu: Przywracamy kolory z globalnego stylu (self.btn_style)
            # Dzięki temu przycisk wróci do wyglądu zgodnego z aktualnym motywem (Light/Dark)
            self.btn_exit.configure(
                border_color=self.btn_style["border_color"],
                text_color=self.btn_style["text_color"],
                fg_color=self.btn_style["fg_color"]
            )

        # Przypisanie funkcji do zdarzeń (Enter = najechanie, Leave = zjechanie)
        self.btn_exit.bind("<Enter>", on_enter_exit)
        self.btn_exit.bind("<Leave>", on_leave_exit)

        # btn_start = tk.Button(self.root, text=self.txt["btn_run"], command=self.open_plan_window, **self.btn_style)
        # btn_start.pack(pady=10)
        self.middle_frame = tk.Frame(self.sidebar)
        self.middle_frame.pack(expand=True)

        # btn_add = tk.Button(self.middle_frame, text=self.txt["btn_add_exam"], command=self.sidebar_add, **self.btn_style)
        # btn_add.pack(pady=5)

        self.btn_status = ctk.CTkButton(self.middle_frame, text=self.txt["btn_toggle_status"], command=self.sidebar_toggle, **self.btn_style)
        self.btn_status.pack(pady=5)

        def on_enter_status(event):
            color = None

            # 1. Logika dla statusu TODO (Zielony)
            if self.status_btn_mode == "todo":
                color = "#2ecc71"

                # 2. Logika dla statusu DONE (Tu robimy poprawkę)
            elif self.status_btn_mode == "done":
                if self.current_theme == "light":
                    color = "#555555"  # Ciemnoszary (dla jasnego tła)
                else:
                    color = "#ffffff"  # Biały (dla ciemnego tła)

            # 3. Logika dla zablokowanych (Czerwony)
            elif self.status_btn_mode == "locked":
                color = "#e74c3c"

                # Zastosowanie koloru
            if color:
                self.btn_status.configure(border_color=color, text_color=color)

        def on_leave_status(event):
            # Przywracamy domyślny styl z motywu
            self.btn_status.configure(
                border_color=self.btn_style["border_color"],
                text_color=self.btn_style["text_color"]
            )

        self.btn_status.bind("<Enter>", on_enter_status)
        self.btn_status.bind("<Leave>", on_leave_status)

        self.btn_edit = ctk.CTkButton(self.middle_frame, text=self.txt["btn_edit"], command=self.sidebar_edit, **self.btn_style)
        self.btn_edit.pack(pady=5)

        def on_enter_edit(event):
            color = None
            # Jeśli tryb to "editable" -> Niebieski
            if self.edit_btn_mode == "editable":
                color = "#3498db"
                # Jeśli tryb to "locked" -> Czerwony
            elif self.edit_btn_mode == "locked":
                color = "#e74c3c"

            if color:
                self.btn_edit.configure(border_color=color, text_color=color)

        def on_leave_edit(event):
            # Powrót do stylu z motywu
            self.btn_edit.configure(
                border_color=self.btn_style["border_color"],
                text_color=self.btn_style["text_color"]
            )

        self.btn_edit.bind("<Enter>", on_enter_edit)
        self.btn_edit.bind("<Leave>", on_leave_edit)
        # btn_arch = tk.Button(self.sidebar, text=self.txt["btn_all_exams"], command=self.sidebar_archive, **self.btn_style)
        # btn_arch.pack(pady=5)
        # btn_man = tk.Button(self.sidebar, text=self.txt["btn_manual"], command=self.open_manual, **self.btn_style)
        # btn_man.pack(pady=10)

        self.plan_container = ctk.CTkFrame(self.root, fg_color="transparent", corner_radius=0)
        self.plan_container.grid(row=0, column=1, sticky="nsew")

        self.plan_view = PlanWindow(parent=self.plan_container, txt=self.txt, data=self.data, btn_style=self.btn_style, dashboard_callback=self.refresh_dashboard, selection_callback=self.update_status_button_state)

        self.sidebar.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.middle_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.label_title.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.stats_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())

        apply_theme(self, self.current_theme)

        #  Pierwsze obliczenie statystyk
        self.refresh_dashboard()

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

    def change_theme(self, theme_name):
        self.data["settings"]["theme"] = theme_name
        save(self.data)
        self.current_theme = theme_name
        apply_theme(self, theme_name)

    # Znajdź tę funkcję i podmień ją na nową wersję:
    def update_status_button_state(self, status_mode, edit_mode="default"):
        # 1. Zapisujemy stan obu przycisków
        self.status_btn_mode = status_mode
        self.edit_btn_mode = edit_mode  # <--- Nowa zmienna stanu

        # 2. Resetujemy wygląd obu przycisków do domyślnego
        self.btn_status.configure(border_color=self.btn_style["border_color"], text_color=self.btn_style["text_color"])
        self.btn_edit.configure(border_color=self.btn_style["border_color"], text_color=self.btn_style["text_color"])

    # Funkcja odświeżająca statystyki na ekranie początkowym
    def refresh_dashboard(self):
        today = date.today()
        # ... (początek funkcji bez zmian) ...
        current_colors = THEMES.get(self.current_theme, THEMES["light"])
        default_text = current_colors["fg_text"]

        # A. Postęp Całkowity
        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= today}
        active_topics = [t for t in self.data["topics"] if t["exam_id"] in active_exams_ids]
        total = len(active_topics)
        done = len([t for t in active_topics if t["status"] == "done"])

        # Obliczamy procenty i wartość float (0.0 - 1.0)
        prog_val = 0.0
        prog_percent = 0
        if total > 0:
            prog_val = done / total
            prog_percent = int(prog_val * 100)

        self.lbl_progress.configure(
            text=self.txt["stats_total_progress"].format(done=done, total=total, progress=prog_percent))

        # AKTUALIZACJA PASKA TOTAL
        self.bar_total.set(prog_val)

        # B. Postęp Dziś
        today_all = [t for t in self.data["topics"] if str(t.get("scheduled_date")) == str(today)]
        t_tot = len(today_all)
        t_don = len([t for t in today_all if t["status"] == "done"])

        if t_tot > 0:
            p_day_val = t_don / t_tot
            p_day_perc = int(p_day_val * 100)

            self.lbl_today.configure(
                text=self.txt["stats_progress_today"].format(done=t_don, total=t_tot, prog=p_day_perc))

            # Kolor tekstu (zielony jak 100%)
            if p_day_perc == 100:
                self.lbl_today.configure(text_color="#00b800")
                self.bar_today.configure(progress_color="#2ecc71")
            else:
                self.lbl_today.configure(text_color=default_text)
                self.bar_today.configure(progress_color="#3498db")

            # AKTUALIZACJA PASKA DZIŚ
            self.bar_today.set(p_day_val)

        else:
            self.lbl_today.configure(text=self.txt["stats_no_today"], text_color="#1f6aa5")
            self.bar_today.set(0)  # Pusty pasek jak nie ma zadań

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

            self.lbl_next_exam.configure(text=text, text_color=color)
        else:
            self.lbl_next_exam.configure(text=self.txt["stats_no_upcoming"], text_color="green")

    # uruchomienie okna z instrukcja
    def open_manual(self):
        ManualWindow(self.root, self.txt, self.btn_style)

    # uruchomienie glownego okna aplikacji
    def open_plan_window(self):
        # dashboard_callback aby po zmianach w planie (np wykonano jakies zadanie) okno powitalne odswiezalo statystyki
        PlanWindow(self.root, self.txt, self.data, self.btn_style, dashboard_callback=self.refresh_dashboard)

# uruchomienie aplikacji
if __name__ == "__main__":
    root = ctk.CTk()
    app = GUI(root)
    root.mainloop()
