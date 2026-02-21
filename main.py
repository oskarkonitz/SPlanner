import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date, datetime
from core.storage import manager, DB_PATH, load_language
from PIL import Image, ImageTk, ImageDraw
import time
import math
from core.planner import date_format
from gui.windows.plan import PlanWindow
from gui.dialogs.manual import ManualWindow
from gui.theme_manager import apply_theme, THEMES
from gui.dialogs.blocked_days import BlockedDaysPanel
from gui.effects import ConfettiEffect, FireworksEffect
from gui.windows.timer import TimerWindow
from gui.windows.achievements import AchievementManager
import threading
from core.updater import check_for_updates
from gui.components.drawers import ToolsDrawer, ContentDrawer
from gui.windows.todo import TodoWindow
from gui.dialogs.subjects_manager import SubjectsManagerPanel
from gui.windows.schedule import SchedulePanel
from gui.windows.grades import GradesPanel
from gui.windows.settings import SettingsWindow
from core.sound import play_event_sound
from gui.windows.archive import ArchivePanel
from gui.dialogs.add_exam import AddExamPanel
from gui.windows.achievements import AchievementsPanel
from gui.dialogs.edit import EditExamPanel, EditTopicPanel
import platform
import ctypes

# Dodaj to przed utworzeniem root = ctk.CTk()
if platform.system() == "Windows":
    try:
        # Ustawienie świadomości DPI dla Windows 8.1 i nowszych
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # Ustawienie świadomości DPI dla starszych systemów Windows
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

VERSION = "2.1.3"


def show_cloud_onboarding():
    # Pobieramy flagę bezpośrednio z obiektu config w managerze
    if manager.config.get("cloud_onboarding_shown", False):
        return

    onboarding = ctk.CTkToplevel(root)
    onboarding.title("Cloud Database Update")
    onboarding.geometry("500x420")
    onboarding.attributes("-topmost", True)
    onboarding.resizable(False, False)

    # UI
    ctk.CTkLabel(onboarding, text="☁️ Cloud Sync is Here!", font=("Arial", 24, "bold")).pack(pady=20)

    msg = (
        "✨ StudyPlanner is now even better with Cloud Sync!\n\n"
        "To sync data with your iPhone:\n"
        "1. Log in to Supabase and create a new project.\n"
        "2. Click 'Open Config Folder' below.\n"
        "3. Open 'schema.sql', copy all content, and paste it into Supabase SQL Editor.\n"
        "4. Fill in URL and API Key in 'config.json' and click Migrate.\n\n"
        "The SQL file is already waiting for you in the folder!"
    )

    ctk.CTkLabel(onboarding, text=msg, wraplength=400, justify="left").pack(pady=10, padx=40)

    btn_frame = ctk.CTkFrame(onboarding, fg_color="transparent")
    btn_frame.pack(fill="x", side="bottom", pady=30, padx=20)

    def open_config():
        import os
        import platform
        import subprocess
        from core.storage import CONFIG_PATH
        config_dir = CONFIG_PATH.parent

        try:
            if platform.system() == "Windows":
                os.startfile(config_dir)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", config_dir])
            else:
                subprocess.Popen(["xdg-open", config_dir])
        except Exception as e:
            print(f"Error opening folder: {e}")

    def continue_local():
        # Zapisujemy flagę do pliku config.json
        manager.mark_onboarding_done()
        onboarding.destroy()

    def start_migration():
        # Pokazujemy okno ładowania
        progress_popup = ctk.CTkToplevel(onboarding)
        progress_popup.title("Migrating...")
        progress_popup.geometry("300x150")
        progress_popup.attributes("-topmost", True)

        lbl_status = ctk.CTkLabel(progress_popup, text="Connecting...")
        lbl_status.pack(pady=20)

        progress_bar = ctk.CTkProgressBar(progress_popup)
        progress_bar.pack(padx=20, fill="x")
        progress_bar.set(0)

        def run():
            # Wywołujemy migrację z StorageManagera
            success, message = manager.perform_cloud_migration(
                progress_callback=lambda m: lbl_status.configure(text=m)
            )

            if success:
                messagebox.showinfo("Success", "Migration complete! Restart the app to work in Cloud Mode.")
                onboarding.destroy()
                root.quit()  # Zalecany restart
            else:
                messagebox.showerror("Migration Error", f"Something went wrong.\n\nError: {message}")
                progress_popup.destroy()

        import threading
        threading.Thread(target=run, daemon=True).start()

    ctk.CTkButton(btn_frame, text="🚀 Migrate Data to Cloud",
                  command=start_migration, fg_color="#27ae60", hover_color="#219150").pack(side="top", fill="x", pady=5)

    ctk.CTkButton(btn_frame, text="Continue Locally", fg_color="transparent",
                  border_width=1, command=continue_local).pack(side="left", expand=True, padx=10)

    ctk.CTkButton(btn_frame, text="Open Config Folder 📂",
                  command=open_config).pack(side="right", expand=True, padx=10)

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent, on_finish_callback):
        super().__init__(parent)
        self.on_finish_callback = on_finish_callback

        self.overrideredirect(True)
        # Zwiększyłem nieco okno, żeby zmieścić logo nad napisem
        self.w, self.h = 450, 320
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{self.w}x{self.h}+{(screen_w - self.w) // 2}+{(screen_h - self.h) // 2}")

        # Standardowy kolor tła CustomTkinter (szary)
        self.bg_color = "#2b2b2b"
        self.configure(fg_color=self.bg_color)

        # Parametry animacji i logo
        self.start_time = time.time()

        # --- POPRAWKA ŚCIEŻKI ---
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "_dev_tools", "source_icon.png")
        # ------------------------

        self.logo_size = (120, 120)
        self.corner_radius = 30
        try:
            # Wstępne przygotowanie logo z zaokrąglonymi rogami
            raw_img = Image.open(icon_path).convert("RGBA")
            self.orig_img = raw_img.resize(self.logo_size, Image.Resampling.LANCZOS)
            self.orig_img = self.add_corners(self.orig_img, self.corner_radius)
        except Exception as e:
            print(f"Błąd ładowania ikony: {e}")
            self.orig_img = None

        # Canvas dla animowanego logo (przezroczysty, na górze)
        self.canvas = tk.Canvas(self, width=self.w, height=180, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(pady=(0, 20))

        # Wewnątrz __init__, po stworzeniu self.canvas:
        self.logo_id = self.canvas.create_image(self.w // 2, 110, image=None, tags="logo")

        # Napis i pasek (teraz spakowane pod logo)
        self.lbl_status = ctk.CTkLabel(
            self,
            text="Inicjalizacja...",
            font=("Arial", 13, "bold"),
            text_color="white",
            height=5
        )
        self.lbl_status.pack(pady=(20, 5))

        self.progress = ctk.CTkProgressBar(
            self,
            mode="indeterminate",
            width=320,
            height=6,
            progress_color="#3498db"
        )
        self.progress.pack(pady=(0, 20))
        self.progress.start()

        self.animate()
        threading.Thread(target=self.run_sync, daemon=True).start()

    def add_corners(self, im, rad):
        """Tworzy maskę dla zaokrąglonych rogów i nakłada ją na obraz."""
        mask = Image.new('L', im.size, 0)
        draw = ImageDraw.Draw(mask)
        # Rysujemy wypełniony biały zaokrąglony prostokąt na czarnej masce
        draw.rounded_rectangle((0, 0, im.size[0], im.size[1]), radius=rad, fill=255)

        # Tworzymy wynikowy obraz z przezroczystym tłem
        out = Image.new('RGBA', im.size, (0, 0, 0, 0))
        out.paste(im, (0, 0), mask)
        return out

    def animate(self):
        if not self.winfo_exists(): return

        t = time.time() - self.start_time

        # Parametry ruchu
        angle = math.sin(t * 1.5) * 6
        zoom = 1.0 + math.cos(t * 2.0) * 0.05
        y_bounce = math.sin(t * 3.0) * 5

        if self.orig_img:
            # 1. Rotacja (używamy expand=True, żeby nie ucięło rogów)
            # Resampling.BICUBIC zapewnia lepszą jakość krawędzi przy obrocie
            rotated_img = self.orig_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)

            # 2. Skalowanie
            nw = int(rotated_img.size[0] * zoom)
            nh = int(rotated_img.size[1] * zoom)
            final_img = rotated_img.resize((nw, nh), Image.Resampling.LANCZOS)

            # 3. AKTUALIZACJA ZAMIAST TWORZENIA
            self.tk_img = ImageTk.PhotoImage(final_img)

            # Podmieniamy samą grafikę w istniejącym obiekcie
            self.canvas.itemconfig(self.logo_id, image=self.tk_img)

            # Aktualizujemy współrzędne (środek x, góra-dół y)
            # Dziękicoords() Tkinter nie musi przeliczać całej warstwy od zera
            self.canvas.coords(self.logo_id, self.w // 2, 110 + y_bounce)

        # 16ms odpowiada ~60 FPS, co daje największą płynność na większości monitorów
        self.after(16, self.animate)

    def run_sync(self):
        from core.storage import manager
        if manager.mode == "cloud":
            manager.sync_down(status_callback=lambda t: self.after(0, lambda: self.lbl_status.configure(
                text=t) if self.winfo_exists() else None))

        time.sleep(1.0)
        self.after(0, self.finish)

    def finish(self):
        try:
            self.progress.stop()
        except:
            pass
        self.destroy()
        self.on_finish_callback()


class GUI:
    def __init__(self, root):
        self.root = root

        self.timer_window = None
        self.current_panel = None  # Zmienna do śledzenia aktywnego widoku pełnoekranowego

        # --- INICJALIZACJA STORAGE MANAGER ---
        # Źródło prawdy: Baza Danych SQLite
        self.storage = manager

        # --- INICJALIZACJA USTAWIEŃ I JĘZYKA ---
        # Pobieramy ustawienia bezpośrednio z bazy
        settings = self.storage.get_settings()
        self.current_theme = settings.get("theme", "light")
        self.current_lang = settings.get("lang", "en")
        self.txt = load_language(self.current_lang)

        # --- STYL PRZYCISKÓW (ZDEFINIOWANY NA POCZĄTKU) ---
        self.btn_style = {
            "font": ("Arial", 13, "bold"),
            "height": 32,
            "corner_radius": 20,
            "fg_color": "#3a3a3a",
            "text_color": "white",
            "hover_color": "#454545",
            "border_color": "#3a3a3a",
            "border_width": 0
        }
        # Helper dla stylów w innych klasach
        self.get_btn_style = lambda: self.btn_style

        # --- INICJALIZACJA STATYSTYK I WALIDACJA ---
        self._initialize_global_stats()
        self._check_new_day_reset()

        # --- MENADŻER OSIĄGNIĘĆ ---
        self.ach_manager = AchievementManager(self.root, self.txt, storage=self.storage)

        # --- FIX: Wyświetlenie zaległych powiadomień po resecie dnia ---
        if hasattr(self, 'pending_unlocks') and self.pending_unlocks:
            self.ach_manager.notification_queue.extend(self.pending_unlocks)
            self.root.after(1000, self.ach_manager.process_queue)

        self.ach_manager.check_all(silent=True)

        #  Konfiguracja okna
        self.root.title(self.txt["app_title"])
        self.root.geometry("1600x850")

        # Uklad grid
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # --- SZUFLADY (DRAWERS) - Muszą być na wierzchu, ale inicjujemy je tutaj ---
        # Prawa szuflada (Formularze)
        self.right_drawer = ContentDrawer(self.root)

        # Inicjalizacja szufladki narzędziowej (Lewa)
        callbacks = {
            "timer": self.open_timer,
            "achievements": self.open_achievements,
            "days_off": self.open_blocked_days,
            "subjects": self.open_subjects_manager,
            "grades": self.open_grades_manager,
            "gen_full": self.menu_gen_plan,
            "gen_new": self.menu_gen_plan_new
        }
        # TERAZ btn_style JEST JUŻ ZDEFINIOWANY
        self.tools_drawer = ToolsDrawer(self.root, self.txt, self.btn_style, callbacks)

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
        # Zmiana: Add Exam otwiera szufladę
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

        # --- MENU: PRZEŁĄCZANIE EGZAMINU ---
        switch_menu = tk.Menu(settings_menu, tearoff=0)
        # Pobieramy zapisaną godzinę bezpośrednio z settings (odświeżone na początku)
        current_switch = settings.get("next_exam_switch_hour", 24)
        self.switch_hour_var = tk.IntVar(value=current_switch)

        hours_options = [12, 14, 16, 18, 20, 22]

        for h in hours_options:
            label = f"{h}{self.txt.get('switch_hour_suffix', ':00')}"
            switch_menu.add_radiobutton(label=label, value=h, variable=self.switch_hour_var,
                                        command=lambda h=h: self.set_switch_hour(h))

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

        badges_menu = tk.Menu(settings_menu, tearoff=0)

        current_badge_mode = settings.get("badge_mode", "default")
        self.badge_mode_var = tk.StringVar(value=current_badge_mode)

        badges_menu.add_radiobutton(
            label=self.txt.get("badge_default", "Default (Count)"),
            value="default",
            variable=self.badge_mode_var,
            command=lambda: self.set_badge_mode("default")
        )

        badges_menu.add_radiobutton(
            label=self.txt.get("badge_dot", "Compact (Dot)"),
            value="dot",
            variable=self.badge_mode_var,
            command=lambda: self.set_badge_mode("dot")
        )

        badges_menu.add_radiobutton(
            label=self.txt.get("badge_off", "Disabled"),
            value="off",
            variable=self.badge_mode_var,
            command=lambda: self.set_badge_mode("off")
        )

        settings_menu.add_cascade(label=self.txt.get("menu_badges", "Badges"), menu=badges_menu)

        settings_menu.add_separator()
        settings_menu.add_command(
            label=self.txt.get("menu_check_updates", "Check for updates"),
            command=lambda: check_for_updates(self.txt, silent=False)
        )

        settings_menu.add_separator()
        settings_menu.add_command(label=self.txt.get("btn_open_settings", "Open Full Settings..."),
                                  command=self.open_settings_window)

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

        self.lbl_daily_time = ctk.CTkLabel(self.stats_frame, text="00:00", font=("Arial", 13, "bold"),
                                           text_color="orange")
        self.lbl_daily_time.pack(pady=(5, 0))

        self.btn_exit = ctk.CTkButton(self.sidebar, text=self.txt["btn_exit"], command=self.on_close, **self.btn_style)
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

        self.middle_frame = tk.Frame(self.sidebar)
        self.middle_frame.pack(expand=True, fill="x", padx=15)

        # Definicja przycisków dynamicznych
        self.btn_1 = ctk.CTkButton(self.middle_frame, text="", **self.btn_style)
        self.btn_1.pack(pady=5, fill="x")

        self.btn_2 = ctk.CTkButton(self.middle_frame, text="", **self.btn_style)
        self.btn_2.pack(pady=5, fill="x")

        self.btn_3 = ctk.CTkButton(self.middle_frame, text="", **self.btn_style)
        self.btn_3.pack(pady=5, fill="x")

        # --- GŁÓWNY KONTENER NA WIDOKI ---
        # Zastępujemy bezpośrednie gridowanie tabview kontenerem, który będzie podmieniał zawartość
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.tabview = ctk.CTkTabview(self.main_container, corner_radius=0)
        self.tabview.pack(fill="both", expand=True)  # Zmienione z grid na pack wewnatrz kontenera
        self.tabview._segmented_button.grid_configure(pady=(10, 5))
        self.tabview._segmented_button.configure(corner_radius=20, height=32)

        self.tabview.configure(command=self.on_tab_change)

        self.tab_plan = self.tabview.add(self.txt.get("tab_plan", "Study Plan"))
        self.tab_todo = self.tabview.add(self.txt.get("tab_todo", "Daily Tasks"))
        self.tab_schedule = self.tabview.add(self.txt.get("lbl_schedule", "Schedule"))

        self.create_badges()

        self.tab_plan.grid_columnconfigure(0, weight=1)
        self.tab_plan.grid_rowconfigure(0, weight=1)
        self.tab_todo.grid_columnconfigure(0, weight=1)
        self.tab_todo.grid_rowconfigure(0, weight=1)
        self.tab_schedule.grid_columnconfigure(0, weight=1)
        self.tab_schedule.grid_rowconfigure(0, weight=1)

        # --- ZAKŁADKA 1: PLAN NAUKI ---
        self.plan_view = PlanWindow(parent=self.tab_plan,
                                    txt=self.txt,
                                    storage=self.storage,
                                    btn_style=self.btn_style,
                                    dashboard_callback=self.refresh_dashboard,
                                    selection_callback=self.update_sidebar_buttons,
                                    drawer_parent=self.root,
                                    content_drawer=self.right_drawer)

        # --- ZAKŁADKA 2: TODO LIST ---
        self.todo_view = TodoWindow(parent=self.tab_todo,
                                    txt=self.txt,
                                    storage=self.storage,
                                    btn_style=self.btn_style,
                                    dashboard_callback=self.refresh_dashboard,
                                    selection_callback=self.update_sidebar_buttons,
                                    drawer_parent=self.root,
                                    drawer=self.right_drawer)

        # --- ZAKLADKA 3: SCHEDULE ---
        self.schedule_view = SchedulePanel(parent=self.tab_schedule,
                                           txt=self.txt,
                                           btn_style=self.btn_style,
                                           storage=self.storage,
                                           subjects_callback=self.open_subjects_manager,
                                           drawer=self.right_drawer) # ZMIANA: Przekazujemy drawer
        self.schedule_view.pack(fill="both", expand=True, padx=10, pady=10)

        # Odznaczanie
        self.update_sidebar_buttons("idle", "idle", "idle")

        self.sidebar.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.middle_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.label_title.bind("<Button-1>", lambda e: self.plan_view.deselect_all())
        self.stats_frame.bind("<Button-1>", lambda e: self.plan_view.deselect_all())

        self.effect_confetti = ConfettiEffect(self.sidebar)
        self.effect_fireworks = FireworksEffect(self.sidebar)

        self.celebration_shown = False

        # Aplikowanie motywu i start
        apply_theme(self, self.current_theme)
        self.fix_treeview_colors()
        self.refresh_dashboard()

        # --- AUTO-UPDATE ---
        threading.Thread(target=lambda: check_for_updates(self.txt, silent=True), daemon=True).start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Configure>", self.on_window_resize)

        # --- SMART STARTUP (NOWA FUNKCJA) ---
        self._perform_smart_startup()

    # --- NAWIGACJA (SPA VIEW SWITCHER) ---
    def switch_to_view(self, panel_class, **kwargs):
        """Przełącza główny kontener z zakładek na pełny widok panelu."""
        # 1. Zamknij szuflady jeśli otwarte
        if self.right_drawer.is_open: self.right_drawer.close_panel()
        if self.tools_drawer.is_open: self.tools_drawer.close_panel()

        # 2. Ukryj zakładki
        self.tabview.pack_forget()

        # 3. Usuń poprzedni panel jeśli istnieje
        if self.current_panel:
            self.current_panel.destroy()
            self.current_panel = None

        # 4. Utwórz nowy panel
        # Wstrzykujemy close_callback, aby panel wiedział jak wrócić
        # ORAZ drawer, aby panel mógł otwierać swoje pod-formularze
        self.current_panel = panel_class(self.main_container,
                                         close_callback=self.restore_dashboard,
                                         drawer=self.right_drawer,
                                         **kwargs)
        self.current_panel.pack(fill="both", expand=True)

    def restore_dashboard(self):
        """Wraca do widoku zakładek."""
        if self.current_panel:
            self.current_panel.destroy()
            self.current_panel = None

        self.tabview.pack(fill="both", expand=True)
        self.refresh_dashboard()

    def _perform_smart_startup(self):
        """
        Logika startowa:
        1. Sprawdź Plan (czy są tematy 'todo' z datą). Jeśli tak -> Otwórz Plan.
        2. Sprawdź ToDo (czy są zadania 'todo'). Jeśli tak -> Otwórz ToDo.
        3. Fallback -> Otwórz Schedule.
        """
        # 1. PLAN
        topics = self.storage.get_topics()
        plan_active = False
        for t in topics:
            if t["status"] == "todo" and t["scheduled_date"]:
                plan_active = True
                break

        if plan_active:
            self.tabview.set(self.txt.get("tab_plan", "Study Plan"))
            return

        # 2. TODO
        tasks = self.storage.get_daily_tasks()
        todo_active = False
        for t in tasks:
            if t["status"] == "todo":
                todo_active = True
                break

        if todo_active:
            self.tabview.set(self.txt.get("tab_todo", "Daily Tasks"))
            return

        # 3. SCHEDULE (Fallback)
        self.tabview.set(self.txt.get("lbl_schedule", "Schedule"))

    def _initialize_global_stats(self):
        """Sprawdza i inicjalizuje brakujące klucze statystyk w bazie danych."""
        gs = self.storage.get_global_stats()
        keys_to_check = [
            ("daily_study_time", 0),
            ("last_study_date", ""),
            ("all_time_best_time", 0),
            ("total_study_time", 0)
        ]
        for key, default in keys_to_check:
            if key not in gs:
                self.storage.update_global_stat(key, default)

    def _check_new_day_reset(self):
        """Obsługuje logikę resetu dziennego (New Day Logic) bezpośrednio na bazie."""
        gs = self.storage.get_global_stats()
        today_str = str(date.today())
        last_date = gs.get("last_study_date", "")

        self.pending_unlocks = []

        if last_date != today_str:
            daily = gs.get("daily_study_time", 0)
            best = gs.get("all_time_best_time", 0)

            # Sprawdź czy był rekord przed resetem
            if daily > best:
                self.storage.update_global_stat("all_time_best_time", daily)
                # Sprawdź osiągnięcie rekordu
                achieved = self.storage.get_achievements()
                if best > 0 and "record_breaker" not in achieved:
                    self.storage.add_achievement("record_breaker")
                    self.pending_unlocks.append(("🚀", "ach_record_breaker", "ach_desc_record_breaker"))

            # Reset na nowy dzień
            self.storage.update_global_stat("daily_study_time", 0)
            self.storage.update_global_stat("last_study_date", today_str)

    def create_badges(self):
        badge_font = ("Arial", 10, "bold")

        self.badge_plan = ctk.CTkLabel(
            self.tabview, text="", width=20, height=20, corner_radius=10,
            font=badge_font, fg_color="transparent", text_color="white"
        )

        self.badge_todo = ctk.CTkLabel(
            self.tabview, text="", width=20, height=20, corner_radius=10,
            font=badge_font, fg_color="transparent", text_color="white"
        )

    def sidebar_add(self):
        # ZMIANA: Zamiast Toplevel -> Szuflada
        self.right_drawer.set_content(AddExamPanel,
                                      txt=self.txt,
                                      btn_style=self.get_btn_style(),
                                      storage=self.storage,
                                      callback=self.refresh_dashboard,
                                      close_callback=self.right_drawer.close_panel)

    def sidebar_toggle(self):
        self.plan_view.toggle_status()

    def sidebar_edit(self):
        self.plan_view.open_edit()

    def sidebar_archive(self):
        # ZMIANA: Zamiast Toplevel -> Switch View
        def edit_exam_wrapper(exam_data, callback):
            self.right_drawer.set_content(EditExamPanel,
                                          txt=self.txt,
                                          btn_style=self.get_btn_style(),
                                          exam_data=exam_data,
                                          storage=self.storage,
                                          callback=callback,
                                          close_callback=self.right_drawer.close_panel)

        def edit_topic_wrapper(topic_data, callback):
            self.right_drawer.set_content(EditTopicPanel,
                                          txt=self.txt,
                                          btn_style=self.get_btn_style(),
                                          topic_data=topic_data,
                                          storage=self.storage,
                                          callback=callback,
                                          close_callback=self.right_drawer.close_panel)

        self.switch_to_view(ArchivePanel,
                            txt=self.txt,
                            btn_style=self.get_btn_style(),
                            edit_exam_func=edit_exam_wrapper,
                            edit_topic_func=edit_topic_wrapper,
                            dashboard_callback=self.refresh_dashboard,
                            storage=self.storage)

    def menu_gen_plan(self):
        self.plan_view.run_and_refresh(only_unscheduled=False)

    def menu_gen_plan_new(self):
        self.plan_view.run_and_refresh(only_unscheduled=True)

    def menu_refresh(self):
        self.plan_view.refresh_table()
        # ZMIANA: Odświeżamy też schedule jeśli aktywne
        if hasattr(self, 'schedule_view'):
            self.schedule_view.load_data()

    def set_badge_mode(self, mode):
        # Aktualizacja w bazie
        self.storage.update_setting("badge_mode", mode)
        # Odświeżamy widok natychmiast
        self.update_badges_logic()

    def on_tab_change(self):
        if hasattr(self, 'plan_view'):
            self.plan_view.deselect_all()
        if hasattr(self, 'todo_view'):
            self.todo_view.deselect_all()
        self.update_sidebar_buttons("idle", "idle", "idle")

    def menu_clear_data(self):
        if messagebox.askyesno(self.txt.get("msg_confirm", "Confirm"),
                               self.txt.get("msg_clear_confirm", "Clear all data?")):
            # 1. Usuwanie danych z Bazy Danych
            existing_exams = self.storage.get_exams()
            for ex in existing_exams:
                self.storage.delete_exam(ex['id'])

            existing_tasks = self.storage.get_daily_tasks()
            for t in existing_tasks:
                self.storage.delete_daily_task(t['id'])

            existing_blocked = self.storage.get_blocked_dates()
            for d in existing_blocked:
                self.storage.remove_blocked_date(d)

            # 2. Resetowanie Statystyk globalnych w Bazie
            reset_stats = {
                "topics_done": 0,
                "notes_added": 0,
                "exams_added": 0,
                "days_off": 0,
                "pomodoro_sessions": 0,
                "activity_started": False,
                "had_overdue": False
            }
            for k, v in reset_stats.items():
                self.storage.update_global_stat(k, v)

            # 3. Odświeżenie widoków (pobiorą puste dane z SQL)
            self.plan_view.refresh_table()
            self.refresh_dashboard()

            # 4. Reset managera osiągnięć
            self.ach_manager = AchievementManager(self.root, self.txt, storage=self.storage)

            messagebox.showinfo(self.txt.get("msg_info", "Info"), self.txt.get("msg_data_cleared", "Data cleared!"))

    def change_language(self, new_code):
        settings = self.storage.get_settings()
        if new_code == settings.get("lang", "en"):
            return
        self.storage.update_setting("lang", new_code)

        restart = messagebox.askyesno(self.txt["msg_info"], self.txt["msg_lang_changed"])
        if restart:
            self.root.destroy()
            os.execl(sys.executable, sys.executable, *sys.argv)

    def set_switch_hour(self, hour):
        self.storage.update_setting("next_exam_switch_hour", hour)
        self.refresh_dashboard()

    def change_theme(self, theme_name):
        self.storage.update_setting("theme", theme_name)
        self.current_theme = theme_name
        apply_theme(self, theme_name)
        self.fix_treeview_colors()

    def open_blocked_days(self):
        # ZMIANA: Zamiast Window -> ContentDrawer
        self.right_drawer.set_content(BlockedDaysPanel,
                                      txt=self.txt,
                                      btn_style=self.get_btn_style(),
                                      callback=self.menu_gen_plan,
                                      refresh_callback=self.refresh_dashboard,
                                      storage=self.storage,
                                      close_callback=self.right_drawer.close_panel)

    def open_subjects_manager(self):
        # ZMIANA: Switch View
        self.switch_to_view(SubjectsManagerPanel,
                            txt=self.txt,
                            btn_style=self.get_btn_style(),
                            storage=self.storage,
                            refresh_callback=self.refresh_dashboard)

    def open_grades_manager(self):
        # ZMIANA: Switch View
        self.switch_to_view(GradesPanel,
                            txt=self.txt,
                            btn_style=self.get_btn_style(),
                            storage=self.storage)

    def open_settings_window(self):
        def on_settings_saved():
            new_theme = self.storage.get_settings().get("theme", "light")
            if new_theme != self.current_theme:
                self.change_theme(new_theme)
            self.refresh_dashboard()
            self.update_badges_logic()

        SettingsWindow(self.root, self.txt, self.btn_style, self.storage, app_version=VERSION,
                       callback_refresh=on_settings_saved)

    def update_sidebar_buttons(self, s1, s2, s3):
        # 1. RESET UI
        self.btn_1.pack_forget()
        self.btn_2.pack_forget()
        self.btn_3.pack_forget()

        def config_btn(btn, mode):
            if mode == "hidden" or mode == "disabled":
                return False

            current_text_col = self.btn_style.get("text_color", "white")
            current_hover = self.btn_style.get("hover_color", "#454545")

            COL_GREEN = "#00b800"
            COL_BLUE = "#3399ff"
            COL_RED = "#e74c3c"
            COL_ORANGE = "#e67e22"

            text = "Button"
            cmd = None
            color = None

            if mode == "idle":
                pass
            elif mode == "add":
                text = self.txt["btn_add_exam"]
                cmd = self.sidebar_add
            elif mode == "archive":
                text = self.txt["win_archive_title"]
                cmd = self.sidebar_archive
            elif mode == "tools":
                text = self.txt.get("btn_tools", "Tools")
                cmd = self.toggle_tools_drawer
            elif mode == "complete":
                text = self.txt.get("tag_done", "Done")
                cmd = self.plan_view.toggle_status
                color = COL_GREEN
            elif mode == "restore":
                text = self.txt.get("btn_restore", "Restore")
                cmd = self.plan_view.restore_status
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
            # --- ZAKŁADKA TODO ---
            elif mode == "todo_complete":
                text = self.txt.get("tag_done", "Done")
                cmd = self.todo_view.toggle_status
                color = COL_GREEN
            elif mode == "todo_restore":
                text = self.txt.get("btn_restore", "Restore")
                cmd = self.todo_view.toggle_status
                if self.current_theme == "dark":
                    color = "#ffffff"
                else:
                    color = "gray"
            elif mode == "todo_delete":
                text = self.txt["btn_delete"]
                cmd = self.todo_view.delete_task
                color = COL_RED

            btn.configure(text=text, command=cmd)

            if color:
                btn.configure(
                    fg_color="transparent",
                    border_color=color,
                    text_color=color,
                    border_width=1.2,
                    hover_color=current_hover
                )
            else:
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
        # ZMIANA: ContentDrawer
        self.right_drawer.set_content(AchievementsPanel,
                                      txt=self.txt,
                                      storage=self.storage,
                                      btn_style=self.btn_style,
                                      close_callback=self.right_drawer.close_panel)

    def open_timer(self):
        if self.timer_window is None or not self.timer_window.winfo_exists():
            self.timer_window = TimerWindow(self.root, self.txt, self.btn_style,
                                            callback=self.refresh_dashboard, storage=self.storage)
        else:
            self.timer_window.lift()

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

    def on_window_resize(self, event):
        if event.widget == self.root:
            self.update_badges_logic()

    def update_badges_logic(self):
        settings = self.storage.get_settings()
        exams = [dict(x) for x in self.storage.get_exams()]
        topics = [dict(x) for x in self.storage.get_topics()]
        daily_tasks = [dict(x) for x in self.storage.get_daily_tasks()]

        mode = settings.get("badge_mode", "default")

        if mode == "off":
            self.badge_plan.place_forget()
            self.badge_todo.place_forget()
            return

        # Ustawienia rozmiaru i offsetu
        if mode == "dot":
            size = 10
            font_size = 1
            offset_y = 0
            offset_x = -15  # Przesunięcie w lewo od krawędzi taba
        else:
            size = 20
            font_size = 10
            offset_y = -8
            offset_x = -10

        self.badge_plan.configure(width=size, height=size, font=("Arial", font_size, "bold"))
        self.badge_todo.configure(width=size, height=size, font=("Arial", font_size, "bold"))

        try:
            # Pobieramy geometrię paska zakładek
            seg_btn = self.tabview._segmented_button
            seg_x = seg_btn.winfo_x()
            seg_y = seg_btn.winfo_y()
            seg_w = seg_btn.winfo_width()
        except AttributeError:
            return

        # --- FIX: OBLICZANIE POZYCJI DLA 3 ZAKŁADEK ---
        # Mamy 3 zakładki, więc szerokość jednej to 1/3 całości
        tab_width = seg_w / 3

        # Tab 1 (Study Plan) kończy się na 1 * tab_width
        plan_x_px = seg_x + tab_width + offset_x

        # Tab 2 (Daily Tasks) kończy się na 2 * tab_width
        todo_x_px = seg_x + (2 * tab_width) + offset_x

        badge_y_px = seg_y + offset_y

        # --- LOGIKA DANYCH (bez zmian) ---
        today = date.today()
        today_str = str(today)

        active_exams_ids = {e["id"] for e in exams if date_format(e["date"]) >= today}
        p_overdue = 0
        p_today_todo = 0
        p_today_done = 0

        for t in topics:
            if t["exam_id"] not in active_exams_ids: continue
            t_date = t.get("scheduled_date")
            if not t_date: continue
            t_date_obj = date_format(t_date)
            if t_date_obj < today and t["status"] == "todo":
                p_overdue += 1
            elif t_date_obj == today:
                if t["status"] == "todo":
                    p_today_todo += 1
                elif t["status"] == "done":
                    p_today_done += 1

        total_p = p_overdue + p_today_todo

        should_show_plan = total_p > 0 or p_today_done > 0
        if should_show_plan:
            color = "#e74c3c" if p_overdue > 0 else ("#e67e22" if p_today_todo > 0 else "#2ecc71")
            text = "" if mode == "dot" else (str(total_p) if total_p > 0 else "✓")
            self.badge_plan.configure(fg_color=color, text=text)
            self.badge_plan.place(x=plan_x_px, y=badge_y_px)
            self.badge_plan.lift()
        else:
            self.badge_plan.place_forget()

        t_overdue = sum(1 for t in daily_tasks
                        if t.get("date", "") != "" and t.get("date", "") < today_str and t["status"] == "todo")
        t_today_todo = sum(1 for t in daily_tasks
                           if t.get("date", "") == today_str and t["status"] == "todo")
        t_today_done = sum(1 for t in daily_tasks
                           if t.get("date", "") == today_str and t["status"] == "done")

        total_t = t_overdue + t_today_todo

        should_show_todo = total_t > 0 or t_today_done > 0
        if should_show_todo:
            color = "#e74c3c" if t_overdue > 0 else ("#e67e22" if t_today_todo > 0 else "#2ecc71")
            text = "" if mode == "dot" else (str(total_t) if total_t > 0 else "✓")
            self.badge_todo.configure(fg_color=color, text=text)
            self.badge_todo.place(x=todo_x_px, y=badge_y_px)
            self.badge_todo.lift()
        else:
            self.badge_todo.place_forget()

    def refresh_dashboard(self):
        # --- PURE SQL: POBIERANIE DANYCH ON-DEMAND ---
        exams = [dict(r) for r in self.storage.get_exams()]
        topics = [dict(r) for r in self.storage.get_topics()]
        daily_tasks = [dict(r) for r in self.storage.get_daily_tasks()]
        global_stats = self.storage.get_global_stats()
        settings = self.storage.get_settings()

        today = date.today()
        today_str = str(today)
        current_colors = THEMES.get(self.current_theme, THEMES["light"])
        default_text = current_colors["fg_text"]

        # 1. PLAN NAUKI
        active_exams_ids = {e["id"] for e in exams if date_format(e["date"]) >= today}
        active_topics = [t for t in topics if t["exam_id"] in active_exams_ids]

        plan_total = len(active_topics)
        plan_done = len([t for t in active_topics if t["status"] == "done"])

        today_plan_all = [t for t in topics if str(t.get("scheduled_date")) == today_str]
        today_plan_total = len(today_plan_all)
        today_plan_done = len([t for t in today_plan_all if t["status"] == "done"])

        # 2. DAILY TASKS
        todo_total = 0
        todo_done = 0
        today_todo_total = 0
        today_todo_done = 0

        for t in daily_tasks:
            t_date = t.get("date", "")
            is_done = t["status"] == "done"

            if not t_date:
                todo_total += 1
                if is_done: todo_done += 1
            elif t_date >= today_str:
                todo_total += 1
                if is_done: todo_done += 1
                if t_date == today_str:
                    today_todo_total += 1
                    if is_done: today_todo_done += 1
            else:
                # Przeszłość: tylko niezrobione (zaległe)
                if not is_done:
                    todo_total += 1

        # 3. SUMOWANIE
        final_total = plan_total + todo_total
        final_done = plan_done + todo_done

        final_today_total = today_plan_total + today_todo_total
        final_today_done = today_plan_done + today_todo_done

        # Wyświetlanie Total
        prog_val = 0.0
        prog_percent = 0
        if final_total > 0:
            prog_val = final_done / final_total
            prog_percent = int(prog_val * 100)

        self.lbl_progress.configure(
            text=self.txt["stats_total_progress"].format(done=final_done, total=final_total, progress=prog_percent))
        self.animate_bar(self.bar_total, prog_val)

        # Wyświetlanie Today
        if final_today_total > 0:
            p_day_val = final_today_done / final_today_total
            p_day_perc = int(p_day_val * 100)

            self.lbl_today.configure(
                text=self.txt["stats_progress_today"].format(done=final_today_done, total=final_today_total,
                                                             prog=p_day_perc))

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

                    # --- ODTWARZANIE DŹWIĘKU "ALL DONE" ---
                    play_event_sound(self.storage, "sound_all_done")
                    # --------------------------------------

                    self.celebration_shown = True
            else:
                self.lbl_today.configure(text_color=default_text)
                self.bar_today.configure(progress_color="#3498db")
                self.celebration_shown = False
            self.animate_bar(self.bar_today, p_day_val)
        else:
            self.lbl_today.configure(text=self.txt["stats_no_today"], text_color="#1f6aa5")
            self.bar_today.set(0)

        # 4. CZAS DZIENNY
        daily_sec = global_stats.get("daily_study_time", 0)
        if daily_sec > 0:
            mins, secs = divmod(daily_sec, 60)
            hours, mins = divmod(mins, 60)
            time_str = f"{hours:02d}:{mins:02d}"
            lbl_prefix = self.txt.get("lbl_daily_focus", "Today's Focus")
            self.lbl_daily_time.configure(text=f"{lbl_prefix}: {time_str}")
            self.lbl_daily_time.pack(pady=(5, 0))
        else:
            self.lbl_daily_time.pack_forget()

        # 5. NAJBLIŻSZY EGZAMIN
        switch_hour = settings.get("next_exam_switch_hour", 24)
        now_hour = datetime.now().hour

        if switch_hour < 24 and now_hour >= switch_hour:
            future_exams = [e for e in exams if date_format(e["date"]) > today]
        else:
            future_exams = [e for e in exams if date_format(e["date"]) >= today]

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

        # 6. OSIĄGNIĘCIA
        if hasattr(self, 'ach_manager'):
            timer_window_open = False
            if self.timer_window is not None and self.timer_window.winfo_exists():
                timer_window_open = True
            is_silent = timer_window_open

            self.ach_manager.check_all(silent=is_silent)

            if not is_silent:
                self.ach_manager.flush_deferred()

        self.update_badges_logic()

        if hasattr(self, 'ach_manager'):
            self.ach_manager.check_all(silent=False)

    def open_manual(self):
        ManualWindow(self.root, self.txt, self.btn_style)

    def open_plan_window(self):
        # Placeholder data
        PlanWindow(self.root, self.txt, self.btn_style,
                   dashboard_callback=self.refresh_dashboard, storage=self.storage)

    def on_close(self):
        if self.timer_window is not None and self.timer_window.winfo_exists():
            if getattr(self.timer_window, "is_running", False):
                msg = self.txt.get("msg_timer_warning", "Pomodoro is running! Are you sure you want to exit?")
                if not messagebox.askyesno(self.txt["msg_warning"], msg):
                    return
        self.root.quit()

    def fix_treeview_colors(self):
        style = ttk.Style()
        style.theme_use("clam")  # Odcina systemowe wymuszanie kolorów!

        is_dark = self.current_theme == "dark"

        # Kolory dopasowane do CustomTkinter
        bg_color = "#2b2b2b" if is_dark else "#f0f0f0"
        text_color = "white" if is_dark else "black"
        sel_bg = "#404040" if is_dark else "#d9d9d9"
        header_bg = "#3a3a3a" if is_dark else "#e5e5e5"

        # Globalna konfiguracja tabeli
        style.configure("Treeview",
                        background=bg_color,
                        fieldbackground=bg_color,
                        foreground=text_color,
                        borderwidth=0)

        style.map("Treeview",
                  background=[("selected", sel_bg)],
                  foreground=[]  # Teraz to GWARANTUJE zachowanie kolorów tagów!
                  )

        # Dopasowanie nagłówków tabel
        style.configure("Treeview.Heading",
                        background=header_bg,
                        foreground=text_color,
                        borderwidth=0)
        style.map("Treeview.Heading", background=[("active", sel_bg)])


if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()


    def start_main_app():
        app = GUI(root)
        root.deiconify()

        # WYWOŁANIE: sekundę po starcie głównej aplikacji
        root.after(1000, show_cloud_onboarding)


    splash = SplashScreen(root, on_finish_callback=start_main_app)
    root.mainloop()