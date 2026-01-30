import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from core.storage import save


class TimerWindow:
    def __init__(self, parent, txt, btn_style, data, callback=None):  # <--- Dodano callback=None
        self.parent = parent
        self.txt = txt
        self.btn_style = btn_style
        self.data = data
        self.callback = callback  # <--- Zapamiętujemy

        # Konfiguracja
        self.WORK_TIME = 25 * 60
        self.BREAK_TIME = 5 * 60
        self.time_left = self.WORK_TIME
        self.total_time_for_progress = self.WORK_TIME

        self.is_running = False
        self.timer_id = None
        self.is_mini_mode = False

        # Okno
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_timer_title", "Timer"))
        self.win.geometry("300x270")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)

        self.win.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_ui()

    def setup_ui(self):
        # 0. Przycisk Mini/Max (Prawy górny róg)
        # --- ZMIANA: Znak "-" zamiast ikony, większa czcionka ---
        self.btn_mini = ctk.CTkButton(self.win, text="—", width=30, height=30,
                                      font=("Arial", 16, "bold"),
                                      fg_color="transparent", text_color="gray", hover_color=("gray90", "gray20"),
                                      command=self.toggle_mini_mode)
        self.btn_mini.place(relx=0.96, rely=0.02, anchor="ne")

        # 1. Wybór trybu (Górna belka)
        self.mode_frame = ctk.CTkFrame(self.win, fg_color="transparent")

        # Padding górny (40) zostaje, bo mówiłeś że jest OK
        self.mode_frame.pack(pady=(40, 5), padx=5)

        self.btn_focus = ctk.CTkButton(self.mode_frame, text=self.txt.get("timer_focus", "Nauka (25m)"),
                                       width=80, height=25,
                                       fg_color="#219653", hover_color="#1e8449",
                                       command=lambda: self.set_mode("work"))
        self.btn_focus.pack(side="left", padx=2)

        self.btn_break = ctk.CTkButton(self.mode_frame, text=self.txt.get("timer_break", "Przerwa (5m)"),
                                       width=80, height=25,
                                       fg_color="#3498db", hover_color="#2980b9",
                                       command=lambda: self.set_mode("break"))
        self.btn_break.pack(side="left", padx=2)

        self.btn_custom = ctk.CTkButton(self.mode_frame, text=self.txt.get("timer_custom", "Własny"),
                                        width=80, height=25,
                                        fg_color="#9b59b6", hover_color="#8e44ad",
                                        command=self.open_custom_dialog)
        self.btn_custom.pack(side="left", padx=2)

        # 2. Wyświetlacz czasu
        self.lbl_time = ctk.CTkLabel(self.win, text=self.format_time(self.WORK_TIME), font=("Arial", 60, "bold"))
        self.lbl_time.pack(pady=(0, 0))

        # 3. Pasek postępu
        self.progress = ctk.CTkProgressBar(self.win, width=240, height=10)
        self.progress.set(1.0)
        self.progress.pack(pady=(10, 10))

        # 4. Przyciski sterowania (Start/Reset)
        self.ctrl_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        self.ctrl_frame.pack(pady=0)

        self.btn_start = ctk.CTkButton(self.ctrl_frame, text=self.txt.get("timer_start", "START"),
                                       width=80, command=self.toggle_timer, **self.btn_style)
        self.btn_start.pack(side="left", padx=5)

        self.btn_reset = ctk.CTkButton(self.ctrl_frame, text=self.txt.get("timer_reset", "RESET"),
                                       width=80, fg_color="gray", hover_color="darkgray",
                                       command=self.reset_timer)
        self.btn_reset.pack(side="left", padx=5)

        # 5. Przycisk Zamknij
        # --- ZMIANA: Usunięto 'side=bottom', teraz jest tuż pod przyciskami wyżej ---
        self.btn_close_win = ctk.CTkButton(self.win, text=self.txt.get("btn_close", "Zamknij"),
                                           width=100, height=25,
                                           fg_color="transparent", border_width=1, border_color="gray",
                                           text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                                           command=self.on_close)
        self.btn_close_win.pack(pady=(10, 10))  # Zwykły pack z małym odstępem
        # --------------------------------------------------------------------------

    # --- TRYB MINI ---
    def toggle_mini_mode(self):
        if not self.is_mini_mode:
            # Włączamy Mini
            self.is_mini_mode = True

            self.mode_frame.pack_forget()
            self.progress.pack_forget()
            self.ctrl_frame.pack_forget()
            self.btn_close_win.pack_forget()

            # --- ZMIANA: Znak "+" ---
            self.btn_mini.configure(text="+")
            self.win.geometry("200x80")

            self.lbl_time.pack(pady=(15, 0))
            self.lbl_time.configure(font=("Arial", 40, "bold"))

        else:
            # Wracamy do Normalnego
            self.is_mini_mode = False

            # --- ZMIANA: Znak "-" ---
            self.btn_mini.configure(text="-")
            self.win.geometry("300x270")  # Powrót do nowej wysokości

            self.lbl_time.configure(font=("Arial", 60, "bold"))
            self.lbl_time.pack_forget()

            self.mode_frame.pack(pady=(40, 5))
            self.lbl_time.pack(pady=(0, 0))
            self.progress.pack(pady=(10, 10))
            self.ctrl_frame.pack(pady=0)
            # Przywracamy przycisk Zamknij (bez side=bottom)
            self.btn_close_win.pack(pady=(10, 10))

    # --- OKNO DIALOGOWE ---
    def open_custom_dialog(self):
        self.stop_timer()

        dialog = ctk.CTkToplevel(self.win)
        dialog.title(self.txt.get("timer_custom_title", "Ustaw czas"))
        dialog.geometry("250x150")

        dialog.attributes("-topmost", True)
        dialog.transient(self.win)
        dialog.lift()
        dialog.focus_force()

        ctk.CTkLabel(dialog, text=self.txt.get("timer_enter_minutes", "Podaj minuty:"), font=("Arial", 12)).pack(
            pady=(20, 5))

        entry = ctk.CTkEntry(dialog, width=100)
        entry.pack(pady=5)
        entry.focus()

        def on_confirm(event=None):
            try:
                minutes = int(entry.get())
                if minutes > 0:
                    seconds = minutes * 60
                    self.time_left = seconds
                    self.total_time_for_progress = seconds

                    self.lbl_time.configure(text_color=("#000000", "#ffffff"))
                    self.update_display()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", self.txt.get("msg_pos_number_err", "Wpisz liczbę dodatnią."))
                    dialog.attributes("-topmost", True)
            except ValueError:
                messagebox.showerror("Error", self.txt.get("msg_number_err", "To nie jest poprawna liczba."))
                dialog.attributes("-topmost", True)

        btn_ok = ctk.CTkButton(dialog, text="OK", width=80, command=on_confirm, **self.btn_style)
        btn_ok.pack(pady=10)
        dialog.bind('<Return>', on_confirm)

    def format_time(self, seconds):
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"

    def set_mode(self, mode):
        self.stop_timer()
        if mode == "work":
            self.time_left = self.WORK_TIME
            self.total_time_for_progress = self.WORK_TIME
            self.lbl_time.configure(text_color=("#000000", "#ffffff"))
        else:
            self.time_left = self.BREAK_TIME
            self.total_time_for_progress = self.BREAK_TIME
            self.lbl_time.configure(text_color="#3498db")

        self.update_display()

    def toggle_timer(self):
        if self.is_running:
            self.stop_timer()
        else:
            self.start_timer()

    def start_timer(self):
        if not self.is_running and self.time_left > 0:
            self.is_running = True
            self.btn_start.configure(text=self.txt.get("timer_pause", "PAUZA"), fg_color="#e74c3c",
                                     hover_color="#c0392b")
            self.count_down()

    def stop_timer(self):
        if self.is_running:
            self.is_running = False
            self.btn_start.configure(text=self.txt.get("timer_start", "START"), fg_color="#1f6aa5",
                                     hover_color="#144870")
            if self.timer_id:
                self.win.after_cancel(self.timer_id)

    def reset_timer(self):
        self.stop_timer()
        self.time_left = self.total_time_for_progress
        self.update_display()
        if self.total_time_for_progress == self.BREAK_TIME:
            self.lbl_time.configure(text_color="#3498db")
        else:
            self.lbl_time.configure(text_color=("#000000", "#ffffff"))

    def count_down(self):
        if self.is_running and self.time_left > 0:
            self.time_left -= 1
            self.update_display()
            self.timer_id = self.win.after(1000, self.count_down)
        elif self.time_left == 0:
            self.finish()

    def update_display(self):
        self.lbl_time.configure(text=self.format_time(self.time_left))

        if self.total_time_for_progress > 0:
            prog = self.time_left / self.total_time_for_progress
        else:
            prog = 0
        self.progress.set(prog)

    def finish(self):
        self.stop_timer()
        self.win.bell()
        self.lbl_time.configure(text="00:00", text_color="green")
        self.progress.set(0)
        self.win.lift()
        self.win.attributes("-topmost", True)

        # Zapis statystyk Pomodoro
        if self.total_time_for_progress == self.WORK_TIME:
            if "stats" not in self.data:
                self.data["stats"] = {}

            current_count = self.data["stats"].get("pomodoro_count", 0)
            self.data["stats"]["pomodoro_count"] = current_count + 1
            save(self.data)

            # --- POPRAWKA: Powiadom główną aplikację o sukcesie (sprawdź osiągnięcia) ---
            if self.callback:
                self.callback()

    def on_close(self):
        self.stop_timer()
        self.win.destroy()