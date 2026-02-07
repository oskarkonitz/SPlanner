import customtkinter as ctk
import calendar
from datetime import date, datetime
from tkinter import messagebox

class BlockedDaysWindow:
    def __init__(self, parent, txt, data, btn_style, callback=None, refresh_callback=None, storage=None):
        self.txt = txt
        # self.data jest ignorowane (zachowane dla kompatybilności sygnatury)
        self.btn_style = btn_style
        self.callback = callback  # Callback dla "Save & Generate"
        self.refresh_callback = refresh_callback  # Callback dla "Save" (odświeżenie dashboardu)
        self.storage = storage  # Instancja StorageManager

        # Inicjalizacja listy - pobieranie z bazy danych
        if self.storage:
            # Storage zwraca listę stringów dat, więc możemy jej użyć bezpośrednio
            self.local_blocked_dates = self.storage.get_blocked_dates()
        else:
            self.local_blocked_dates = []

        # Tworzymy kopię listy, aby operować lokalnie przed zapisem
        self.local_blocked_dates = list(self.local_blocked_dates)

        self.current_date = date.today()
        self.year = self.current_date.year
        self.month = self.current_date.month

        # --- KONFIGURACJA OKNA ---
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_blocked_title", "Manage Days Off"))
        self.win.geometry("550x600")
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)

        # --- NAGŁÓWKI ---
        header_text = self.txt.get("lbl_blocked_header", "Select days off:")
        legend_text = self.txt.get("lbl_blocked_legend", "(Red = Off)")

        ctk.CTkLabel(self.win, text=header_text, font=("Arial", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(self.win, text=legend_text, font=("Arial", 12), text_color="gray").pack(pady=(0, 10))

        # --- NAWIGACJA ---
        nav_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        nav_frame.pack(fill="x", padx=20, pady=5)

        self.btn_prev = ctk.CTkButton(nav_frame, text="<", width=40, command=self.prev_month)
        self.btn_prev.pack(side="left")

        self.lbl_month_year = ctk.CTkLabel(nav_frame, text="Month Year", font=("Arial", 16, "bold"))
        self.lbl_month_year.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(nav_frame, text=">", width=40, command=self.next_month)
        self.btn_next.pack(side="right")

        # --- KALENDARZ ---
        self.cal_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        self.cal_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for i in range(7):
            self.cal_frame.grid_columnconfigure(i, weight=1)

        self.draw_calendar()

        # --- PRZYCISKI DOLNE ---
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=20, side="bottom")

        # 1. ZAPISZ
        self.btn_save = ctk.CTkButton(
            btn_frame,
            text=self.txt.get("btn_save", "Save"),
            command=self.action_save_only,
            **self.btn_style
        )
        self.btn_save.pack(side="left", padx=5)

        # 2. ZAPISZ I GENERUJ
        lbl_save_gen = self.txt.get("btn_save_gen", "Save & Generate")
        self.btn_save_gen = ctk.CTkButton(
            btn_frame,
            text=lbl_save_gen,
            command=self.action_save_and_gen,
            **self.btn_style
        )
        self.btn_save_gen.pack(side="left", padx=5)

        # 3. ANULUJ
        self.btn_cancel = ctk.CTkButton(
            btn_frame,
            text=self.txt.get("btn_cancel", "Cancel"),
            command=self.win.destroy,
            **self.btn_style
        )
        self.btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        self.btn_cancel.pack(side="left", padx=5)

    def draw_calendar(self):
        for widget in self.cal_frame.winfo_children():
            widget.destroy()

        default_months = list(calendar.month_name)[1:]
        months_list = self.txt.get("months", default_months)
        if len(months_list) < 12: months_list = default_months
        current_month_name = months_list[self.month - 1]
        self.lbl_month_year.configure(text=f"{current_month_name} {self.year}")

        default_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        days_list = self.txt.get("days_short", default_days)
        if len(days_list) < 7: days_list = default_days

        for idx, day in enumerate(days_list):
            lbl = ctk.CTkLabel(self.cal_frame, text=day, font=("Arial", 12, "bold"), width=50)
            lbl.grid(row=0, column=idx, padx=2, pady=5)

        month_days = calendar.monthcalendar(self.year, self.month)

        row_idx = 1
        for week in month_days:
            for col_idx, day_num in enumerate(week):
                if day_num != 0:
                    date_str = f"{self.year}-{self.month:02d}-{self.day_to_str(day_num)}"
                    is_blocked = date_str in self.local_blocked_dates

                    btn_color = "#e74c3c" if is_blocked else "transparent"
                    hover_color = "#c0392b" if is_blocked else None
                    fg_text = "white" if is_blocked else None
                    border_w = 0 if is_blocked else 1

                    if date_str == str(date.today()) and not is_blocked:
                        border_color = "#3498db"
                        border_w = 2
                    else:
                        border_color = "gray"

                    btn = ctk.CTkButton(
                        self.cal_frame,
                        text=str(day_num),
                        width=50,
                        height=40,
                        fg_color=btn_color,
                        hover_color=hover_color,
                        border_color=border_color,
                        border_width=border_w,
                        text_color=fg_text,
                        command=lambda d=date_str: self.toggle_day(d)
                    )

                    if not is_blocked:
                        btn.configure(text_color=("black", "white"))

                    btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)

            row_idx += 1

    def day_to_str(self, d):
        return f"{d:02d}"

    def toggle_day(self, date_str):
        if date_str in self.local_blocked_dates:
            self.local_blocked_dates.remove(date_str)
        else:
            self.local_blocked_dates.append(date_str)
        self.draw_calendar()

    def prev_month(self):
        self.month -= 1
        if self.month == 0:
            self.month = 12
            self.year -= 1
        self.draw_calendar()

    def next_month(self):
        self.month += 1
        if self.month == 13:
            self.month = 1
            self.year += 1
        self.draw_calendar()

    def _update_stats_and_save(self):
        if not self.storage:
            return

        # 1. Synchronizacja listy zablokowanych dat
        # Pobieramy stan aktualny z bazy, aby wyliczyć różnice
        current_db_dates = set(self.storage.get_blocked_dates())
        new_local_dates = set(self.local_blocked_dates)

        days_to_add = new_local_dates - current_db_dates
        days_to_remove = current_db_dates - new_local_dates

        # Usuwamy odznaczone
        for d in days_to_remove:
            self.storage.remove_blocked_date(d)

        # Dodajemy nowe
        for d in days_to_add:
            self.storage.add_blocked_date(d)

        # 2. Aktualizacja statystyk (Global Stats - days_off)
        # Zwiększamy licznik 'days_off' o liczbę nowo dodanych dni wolnych
        count_added = len(days_to_add)

        if count_added > 0:
            stats = self.storage.get_global_stats()
            current_count = stats.get("days_off", 0)

            # Zabezpieczenie typu
            if isinstance(current_count, str):
                try:
                    current_count = int(current_count)
                except ValueError:
                    current_count = 0

            new_count = current_count + count_added
            self.storage.update_global_stat("days_off", new_count)

    def action_save_only(self):
        self._update_stats_and_save()
        self.win.destroy()
        # Wywołujemy odświeżanie dashboardu po zapisie
        if self.refresh_callback:
            self.refresh_callback()

    def action_save_and_gen(self):
        self._update_stats_and_save()
        self.win.destroy()
        if self.callback:
            self.callback()