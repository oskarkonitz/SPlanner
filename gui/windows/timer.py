import customtkinter as ctk
from tkinter import messagebox


class TimerWindow:
    def __init__(self, parent, txt, btn_style, storage=None, callback=None):
        self.parent = parent
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage  # Instancja StorageManager
        self.callback = callback

        self.session_completed = False
        self.is_running = False
        self.timer_id = None
        self.is_mini_mode = False

        self.mode = "pomo"

        self.WORK_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        self.time_left = self.WORK_TIME
        self.total_time_for_progress = self.WORK_TIME

        self.stopwatch_seconds = 0

        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_timer_title", "Timer"))
        self.win.geometry("300x340")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_ui()

    def setup_ui(self):
        # 1. Przełącznik trybów (TAB)
        self.tab_mode = ctk.CTkSegmentedButton(self.win,
                                               values=[self.txt.get("timer_tab_pomo", "Pomodoro"),
                                                       self.txt.get("timer_tab_stopwatch", "Stopwatch")],
                                               command=self.switch_tab)
        self.tab_mode.set(self.txt.get("timer_tab_pomo", "Pomodoro"))

        # 2. SEKCJA POMODORO
        self.frame_pomo = ctk.CTkFrame(self.win, fg_color="transparent")

        self.mode_frame = ctk.CTkFrame(self.frame_pomo, fg_color="transparent")

        self.btn_focus = ctk.CTkButton(self.mode_frame, text=self.txt.get("timer_focus", "Focus"), width=70, height=25,
                                       fg_color="#219653", hover_color="#1e8449",
                                       command=lambda: self.set_pomo_mode("work"))
        self.btn_focus.pack(side="left", padx=2)
        self.btn_break = ctk.CTkButton(self.mode_frame, text=self.txt.get("timer_break", "Break"), width=70, height=25,
                                       fg_color="#3498db", hover_color="#2980b9",
                                       command=lambda: self.set_pomo_mode("break"))
        self.btn_break.pack(side="left", padx=2)
        self.btn_custom = ctk.CTkButton(self.mode_frame, text=self.txt.get("timer_custom", "Custom"), width=70,
                                        height=25,
                                        fg_color="#9b59b6", hover_color="#8e44ad", command=self.open_custom_dialog)
        self.btn_custom.pack(side="left", padx=2)

        self.pomo_center_frame = ctk.CTkFrame(self.frame_pomo, fg_color="transparent")
        self.lbl_time = ctk.CTkLabel(self.pomo_center_frame, text=self.format_time(self.WORK_TIME),
                                     font=("Arial", 60, "bold"))
        self.progress = ctk.CTkProgressBar(self.pomo_center_frame, width=240, height=10)
        self.progress.set(1.0)

        # 3. SEKCJA STOPER
        self.frame_stopwatch = ctk.CTkFrame(self.win, fg_color="transparent")
        self.stopwatch_center_frame = ctk.CTkFrame(self.frame_stopwatch, fg_color="transparent")
        self.lbl_stopwatch = ctk.CTkLabel(self.stopwatch_center_frame, text="00:00:00", font=("Arial", 50, "bold"),
                                          text_color="#e67e22")
        self.lbl_daily_sum = ctk.CTkLabel(self.stopwatch_center_frame, text="Daily: 00:00", font=("Arial", 12),
                                          text_color="gray")

        # 4. WSPÓLNE STEROWANIE
        self.ctrl_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        self.btn_start = ctk.CTkButton(self.ctrl_frame, text=self.txt.get("timer_start", "START"), width=80,
                                       command=self.toggle_timer, **self.btn_style)
        self.btn_start.pack(side="left", padx=5)
        self.btn_reset = ctk.CTkButton(self.ctrl_frame, text=self.txt.get("timer_reset", "RESET"), width=80,
                                       fg_color="gray", hover_color="darkgray", command=self.reset_timer)
        self.btn_reset.pack(side="left", padx=5)

        # 5. Dolny przycisk Close
        txt_col = self.btn_style.get("text_color", "black")
        hover_col = self.btn_style.get("hover_color", "gray")
        self.btn_close_bottom = ctk.CTkButton(self.win, text=self.txt.get("btn_close", "Close"),
                                              width=60, height=20,
                                              fg_color="transparent",
                                              border_width=1,
                                              border_color=txt_col,
                                              text_color=txt_col,
                                              hover_color=hover_col,
                                              font=("Arial", 11),
                                              command=self.on_close)

        # 6. PRZYCISK MINI-MODE
        self.btn_mini = ctk.CTkButton(self.win, text="—", width=30, height=30, font=("Arial", 16, "bold"),
                                      fg_color="transparent", text_color="gray", hover_color=("gray90", "gray20"),
                                      command=self.toggle_mini_mode)
        self.btn_mini.place(relx=0.96, rely=0.02, anchor="ne")

        # Inicjalne pakowanie
        self.repack_normal_mode()

    def repack_normal_mode(self):
        """Przywraca pełny widok okna, resetując kolejność pakowania."""

        # 1. Czyścimy GŁÓWNE kontenery
        self.tab_mode.pack_forget()
        self.frame_pomo.pack_forget()
        self.frame_stopwatch.pack_forget()
        self.ctrl_frame.pack_forget()
        self.btn_close_bottom.pack_forget()

        # 2. Zakładki (GÓRA)
        self.tab_mode.pack(side="top", pady=(10, 5), padx=10)

        # 3. Stopka (DÓŁ - Pakujemy zanim zapakujemy środek z expand=True!)
        self.btn_close_bottom.pack(side="bottom", pady=(0, 15))
        self.ctrl_frame.pack(side="bottom", pady=(5, 5))

        # 4. Środek (Wypełnienie)
        if self.mode == "pomo":
            # --- POPRAWKA: Czyścimy wewnętrzne elementy Pomodoro, aby wymusić kolejność ---
            self.mode_frame.pack_forget()
            self.pomo_center_frame.pack_forget()

            # Teraz pakujemy w dobrej kolejności:
            self.mode_frame.pack(side="top", pady=(10, 5), padx=5)  # Przyciski na górze ramki

            # Resetujemy pozycje w kontenerze centrującym
            self.lbl_time.configure(font=("Arial", 60, "bold"))
            self.lbl_time.pack(expand=True, anchor="s", pady=(0, 5))
            self.progress.pack(expand=True, anchor="n", pady=(5, 0))

            self.pomo_center_frame.pack(fill="both", expand=True)  # Kontener pośrodku
            self.frame_pomo.pack(fill="both", expand=True)  # Główna ramka
        else:
            # --- POPRAWKA: Czyścimy wewnętrzne elementy Stopera ---
            self.stopwatch_center_frame.pack_forget()

            # Przywracamy elementy wewnątrz Stopera
            self.stopwatch_center_frame.pack(fill="both", expand=True)

            self.lbl_stopwatch.configure(font=("Arial", 50, "bold"))
            self.lbl_stopwatch.pack(expand=True, anchor="s", pady=(0, 5))
            self.lbl_daily_sum.pack(expand=True, anchor="n", pady=(5, 0))

            self.frame_stopwatch.pack(fill="both", expand=True)

        # Wyciągamy przycisk mini na wierzch
        self.btn_mini.lift()

    def toggle_mini_mode(self):
        if not self.is_mini_mode:
            # --- PRZEJŚCIE DO MINI ---
            self.is_mini_mode = True
            self.btn_mini.configure(text="+")
            self.win.geometry("220x90")

            # Ukrywamy zewnętrzne elementy
            self.tab_mode.pack_forget()
            self.ctrl_frame.pack_forget()
            self.btn_close_bottom.pack_forget()

            if self.mode == "pomo":
                # Ukrywamy przyciski i pasek, zostawiamy kontener
                self.mode_frame.pack_forget()
                self.progress.pack_forget()

                # Zmieniamy styl i pozycję licznika (nadal w pomo_center_frame)
                self.lbl_time.configure(font=("Arial", 45, "bold"))
                # W trybie mini centrujemy go idealnie
                self.lbl_time.pack_configure(anchor="center", pady=(15, 0))
            else:
                self.lbl_daily_sum.pack_forget()

                self.lbl_stopwatch.configure(font=("Arial", 35, "bold"))
                self.lbl_stopwatch.pack_configure(anchor="center", pady=(15, 0))

        else:
            # --- POWRÓT DO NORMAL ---
            self.is_mini_mode = False
            self.btn_mini.configure(text="—")
            self.win.geometry("300x340")

            # Przywracamy pełny układ (to naprawi kolejność)
            self.repack_normal_mode()

    def switch_tab(self, value):
        self.stop_timer()

        if self.is_mini_mode:
            self.toggle_mini_mode()  # Wyjście z mini przy zmianie zakładki

        if value == self.txt.get("timer_tab_pomo", "Pomodoro"):
            self.mode = "pomo"
        else:
            self.mode = "stopwatch"
            self.update_daily_sum_label()

        self.repack_normal_mode()

    def update_daily_sum_label(self):
        # Pobieranie statystyk z Storage (zamiast self.data)
        if self.storage:
            stats = self.storage.get_global_stats()
            daily_sec = stats.get("daily_study_time", 0)
        else:
            daily_sec = 0

        # Zabezpieczenie typu
        try:
            daily_sec = int(daily_sec)
        except ValueError:
            daily_sec = 0

        mins, secs = divmod(daily_sec, 60)
        hours, mins = divmod(mins, 60)
        self.lbl_daily_sum.configure(text=f"Total Today: {hours:02d}:{mins:02d}")

    # --- LOGIKA CZASU I STORAGE ---

    def increment_daily_stats(self):
        if not self.storage: return

        # 1. Pobieramy aktualne statystyki z bazy
        stats = self.storage.get_global_stats()
        current_daily = stats.get("daily_study_time", 0)
        current_total = stats.get("total_study_time", 0)

        # Konwersja na int na wypadek błędów
        try:
            current_daily = int(current_daily)
            current_total = int(current_total)
        except ValueError:
            current_daily = 0
            current_total = 0

        # 2. Inkrementacja
        new_daily = current_daily + 1
        new_total = current_total + 1

        # 3. Zapis bezpośredni do bazy (bez buforowania w self.data)
        self.storage.update_global_stat("daily_study_time", new_daily)
        self.storage.update_global_stat("total_study_time", new_total)

        # 4. Callback dla odświeżenia głównego okna
        if self.callback: self.callback()

    def toggle_timer(self):
        if self.is_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        if not self.is_running:
            if self.mode == "pomo" and self.time_left <= 0: return
            self.is_running = True
            self.btn_start.configure(text=self.txt.get("timer_pause", "PAUSE"), fg_color="#e74c3c",
                                     hover_color="#c0392b")
            if self.mode == "pomo":
                self.count_down()
            else:
                self.count_up()

    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            self.btn_start.configure(text=self.txt.get("timer_start", "START"), fg_color="#1f6aa5",
                                     hover_color="#144870")
            if self.timer_id: self.win.after_cancel(self.timer_id)

            if self.callback: self.callback()

    def reset_timer(self):
        self.stop_timer()
        if self.mode == "pomo":
            self.time_left = self.total_time_for_progress
            self.update_pomo_display()
        else:
            self.stopwatch_seconds = 0
            self.lbl_stopwatch.configure(text="00:00:00")

    def count_down(self):
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            self.update_pomo_display()
            is_break = (self.total_time_for_progress == self.BREAK_TIME)
            if not is_break: self.increment_daily_stats()
            self.timer_id = self.win.after(1000, self.count_down)
        elif self.time_left == 0:
            self.finish_pomo()

    def update_pomo_display(self):
        self.lbl_time.configure(text=self.format_time(self.time_left))
        prog = self.time_left / self.total_time_for_progress if self.total_time_for_progress > 0 else 0
        self.progress.set(prog)

    def set_pomo_mode(self, mode):
        self.stop_timer()
        if mode == "work":
            self.time_left = self.WORK_TIME
            self.total_time_for_progress = self.WORK_TIME
            self.lbl_time.configure(text_color=("#000000", "#ffffff"))
        else:
            self.time_left = self.BREAK_TIME
            self.total_time_for_progress = self.BREAK_TIME
            self.lbl_time.configure(text_color="#3498db")
        self.update_pomo_display()

    def count_up(self):
        if self.is_running:
            self.stopwatch_seconds += 1
            m, s = divmod(self.stopwatch_seconds, 60)
            h, m = divmod(m, 60)
            self.lbl_stopwatch.configure(text=f"{h:02d}:{m:02d}:{s:02d}")

            self.increment_daily_stats()

            if self.stopwatch_seconds % 60 == 0:
                self.update_daily_sum_label()

            self.timer_id = self.win.after(1000, self.count_up)

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def open_custom_dialog(self):
        self.stop_timer()
        dialog = ctk.CTkToplevel(self.win)
        dialog.title("Set Time")
        dialog.geometry("250x150")
        dialog.attributes("-topmost", True)
        ctk.CTkLabel(dialog, text="Minutes:", font=("Arial", 12)).pack(pady=(20, 5))
        entry = ctk.CTkEntry(dialog, width=100)
        entry.pack(pady=5);
        entry.focus()

        def on_confirm(event=None):
            try:
                mins = int(entry.get())
                if mins > 0:
                    self.time_left = mins * 60
                    self.total_time_for_progress = self.time_left
                    self.update_pomo_display()
                    dialog.destroy()
            except:
                pass

        ctk.CTkButton(dialog, text="OK", width=80, command=on_confirm).pack(pady=10)
        dialog.bind('<Return>', on_confirm)

    def finish_pomo(self):
        self.stop_timer()
        self.win.bell()
        self.lbl_time.configure(text="00:00", text_color="green")

        mins = self.total_time_for_progress / 60
        if mins >= 20:
            earned = max(1, int(mins / 25))

            if self.storage:
                # Update Storage (SQL)
                stats = self.storage.get_global_stats()
                current_sessions = stats.get("pomodoro_sessions", 0)
                try:
                    current_sessions = int(current_sessions)
                except ValueError:
                    current_sessions = 0

                new_sessions = current_sessions + earned
                self.storage.update_global_stat("pomodoro_sessions", new_sessions)

            self.session_completed = True
        self.win.attributes("-topmost", True)

    def on_close(self):
        # 1. Zatrzymujemy timer
        self.stop_timer()

        # 2. Niszczymy okno
        self.win.destroy()

        # 3. ZAWSZE wywołujemy callback po zniszczeniu okna.
        if self.callback:
            self.callback()

    def winfo_exists(self):
        for attr in ['window', 'win', 'root', 'toplevel']:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj and hasattr(obj, 'winfo_exists'):
                    try:
                        return bool(obj.winfo_exists())
                    except:
                        return False
        return False

    def lift(self):
        for attr in ['window', 'win', 'root', 'toplevel']:
            if hasattr(self, attr):
                obj = getattr(self, attr)
                if obj and hasattr(obj, 'lift'):
                    try:
                        obj.lift();
                        return
                    except:
                        pass