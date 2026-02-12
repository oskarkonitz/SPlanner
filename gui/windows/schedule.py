import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime, timedelta, date
from gui.dialogs.subjects_manager import SubjectsManagerPanel
from gui.dialogs.add_exam import AddExamPanel
from gui.dialogs.blocked_days import BlockedDaysPanel
from gui.dialogs.edit import EditExamPanel

# Stałe konfiguracyjne
START_HOUR = 7  # Początek osi czasu (7:00)
END_HOUR = 22  # Koniec osi czasu (22:00)
PX_PER_HOUR = 60  # Wysokość jednej godziny w pikselach
EXAM_DURATION_HOURS = 1.5  # Domyślny czas trwania kafelka egzaminu (dla wizualizacji)
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SchedulePanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, subjects_callback=None, drawer=None):
        # 1. GŁÓWNY KONTENER
        super().__init__(parent, fg_color="transparent")

        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.subjects_callback = subjects_callback
        self.drawer = drawer  # ZMIANA: Dodano obsługę szuflady

        self.current_semester_id = None
        self.semesters = []
        self.subjects_cache = {}
        self.cancellations = set()

        # Oblicz start bieżącego tygodnia
        today = date.today()
        self.current_week_monday = today - timedelta(days=today.weekday())

        # --- GÓRNY PASEK (PRZYCISKI) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(self.top_frame, text=self.txt.get("lbl_schedule", "Schedule"),
                     font=("Arial", 20, "bold")).pack(side="left", padx=5)

        self.combo_sem = ctk.CTkComboBox(self.top_frame, width=180, command=self.on_semester_change)
        self.combo_sem.pack(side="left", padx=10)

        nav_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        nav_frame.pack(side="left", padx=20)

        ctk.CTkButton(nav_frame, text="<", width=30, height=28,
                      fg_color="transparent", border_width=1, border_color="gray",
                      text_color=("gray10", "gray90"),
                      command=self.prev_week).pack(side="left", padx=2)

        self.lbl_week_date = ctk.CTkLabel(nav_frame, text="", width=180, font=("Arial", 12, "bold"))
        self.lbl_week_date.pack(side="left", padx=5)

        ctk.CTkButton(nav_frame, text=">", width=30, height=28,
                      fg_color="transparent", border_width=1, border_color="gray",
                      text_color=("gray10", "gray90"),
                      command=self.next_week).pack(side="left", padx=2)

        ctk.CTkButton(nav_frame, text=self.txt.get("btn_today", "Today"), width=60, height=28,
                      command=self.go_to_today).pack(side="left", padx=10)

        ctk.CTkButton(self.top_frame, text=self.txt.get("btn_edit_subjects", "Edit Subjects"),
                      command=self.open_subjects_manager,
                      width=120, height=30,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=5)

        self.border_frame = ctk.CTkFrame(self, fg_color="transparent",
                                         border_width=1,
                                         border_color=("gray70", "white"),
                                         corner_radius=8)
        self.border_frame.pack(fill="both", expand=True)

        self.header_frame = ctk.CTkFrame(self.border_frame, height=30, corner_radius=0, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=3, pady=(3, 0))

        ctk.CTkFrame(self.header_frame, width=50, height=30, fg_color="transparent").pack(side="left")

        self.day_labels = []
        for i in range(7):
            lbl = ctk.CTkLabel(self.header_frame, text="", font=("Arial", 12, "bold"))
            lbl.pack(side="left", expand=True, fill="x")
            self.day_labels.append(lbl)

        self.scroll_frame = ctk.CTkScrollableFrame(self.border_frame, corner_radius=6, fg_color=("white", "#2b2b2b"))
        self.scroll_frame.pack(fill="both", expand=True, padx=3, pady=3)

        total_height = (END_HOUR - START_HOUR) * PX_PER_HOUR + 50
        self.grid_area = ctk.CTkFrame(self.scroll_frame, height=total_height, fg_color="transparent")
        self.grid_area.pack(fill="x", expand=True)

        # ZMIANA: Obsługa PPM na siatce
        self.grid_area.bind("<Button-3>", self.on_grid_right_click)
        if self._tk_ws() == "aqua":
             self.grid_area.bind("<Button-2>", self.on_grid_right_click)

        self._draw_grid_lines()
        self.load_data()

    def _draw_grid_lines(self):
        for i, hour in enumerate(range(START_HOUR, END_HOUR + 1)):
            y = i * PX_PER_HOUR
            time_str = f"{hour:02d}:00"
            ctk.CTkLabel(self.grid_area, text=time_str, text_color="gray", font=("Arial", 10)).place(x=5, y=y - 7)

            if i > 0:
                sep = ctk.CTkFrame(self.grid_area, height=1, fg_color=("gray80", "gray40"))
                sep.place(x=50, y=y, relwidth=1.0)

    def update_week_label(self):
        monday = self.current_week_monday
        sunday = monday + timedelta(days=6)
        txt = f"{monday.strftime('%d.%m')} - {sunday.strftime('%d.%m.%Y')}"
        self.lbl_week_date.configure(text=txt)

        today = date.today()

        for i, lbl in enumerate(self.day_labels):
            day_date = monday + timedelta(days=i)
            day_name = self.txt.get(f"day_{DAYS[i].lower()}", DAYS[i])
            lbl.configure(text=f"{day_name} {day_date.strftime('%d.%m')}")

            # ZMIANA: Podkreślenie zamiast zmiany koloru
            if day_date == today:
                 lbl.configure(font=("Arial", 12, "bold", "underline"))
            else:
                 lbl.configure(font=("Arial", 12, "bold"))

    def prev_week(self):
        self.current_week_monday -= timedelta(days=7)
        self.refresh_schedule()

    def next_week(self):
        self.current_week_monday += timedelta(days=7)
        self.refresh_schedule()

    def go_to_today(self):
        today = date.today()
        self.current_week_monday = today - timedelta(days=today.weekday())
        self.refresh_schedule()

    def load_data(self):
        self.semesters = [dict(s) for s in self.storage.get_semesters()]
        self.semesters.sort(key=lambda x: not x["is_current"])

        all_label = self.txt.get("val_all", "All")
        sem_names = [s["name"] for s in self.semesters]
        values = [all_label] + sem_names

        self.combo_sem.configure(values=values)

        if self.semesters:
            if not self.current_semester_id:
                self.current_semester_id = self.semesters[0]["id"]
                self.combo_sem.set(self.semesters[0]["name"])
            elif self.current_semester_id == "ALL":
                self.combo_sem.set(all_label)
            else:
                current_name = next((s["name"] for s in self.semesters if s["id"] == self.current_semester_id), None)
                if current_name:
                    self.combo_sem.set(current_name)
                else:
                    self.current_semester_id = self.semesters[0]["id"]
                    self.combo_sem.set(self.semesters[0]["name"])
        else:
            self.combo_sem.set(all_label)
            self.current_semester_id = "ALL"

        self.refresh_schedule()

    def on_semester_change(self, choice):
        all_label = self.txt.get("val_all", "All")

        if choice == all_label:
            self.current_semester_id = "ALL"
        else:
            sem = next((s for s in self.semesters if s["name"] == choice), None)
            if sem:
                self.current_semester_id = sem["id"]

        self.refresh_schedule()

    def open_subjects_manager(self):
        # ZMIANA: Użycie callbacku lub fallback
        if self.subjects_callback:
            self.subjects_callback()
        else:
            # Fallback (gdyby main nie podał callbacku) - tworzymy okno modalne z panelem
            top = ctk.CTkToplevel(self)
            top.title(self.txt.get("win_subj_man_title", "Subjects"))
            top.geometry("1000x700")
            SubjectsManagerPanel(top, self.txt, self.btn_style, self.storage,
                                 refresh_callback=self.load_data).pack(fill="both", expand=True)

    def refresh_schedule(self):
        self.update_week_label()

        for widget in self.grid_area.winfo_children():
            if isinstance(widget, ctk.CTkButton) or \
                    (isinstance(widget, ctk.CTkFrame) and (
                            getattr(widget, "is_marker", False) or getattr(widget, "is_block", False))):
                widget.destroy()

        if not self.current_semester_id: return

        if self.current_semester_id == "ALL":
            raw_subjects = self.storage.get_subjects(None)
        else:
            raw_subjects = self.storage.get_subjects(self.current_semester_id)

        self.subjects_cache = {s["id"]: dict(s) for s in raw_subjects}
        semester_subj_ids = set(self.subjects_cache.keys())

        raw_cancels = self.storage.get_schedule_cancellations()
        self.cancellations = {(c["entry_id"], c["date"]) for c in raw_cancels}

        all_schedule = [dict(x) for x in self.storage.get_schedule()]

        for entry in all_schedule:
            self._process_and_draw_entry(entry)

        all_exams = [dict(e) for e in self.storage.get_exams()]
        week_end = self.current_week_monday + timedelta(days=6)

        for exam in all_exams:
            if exam.get("subject_id") not in semester_subj_ids:
                continue

            try:
                exam_date = datetime.strptime(exam["date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            if self.current_week_monday <= exam_date <= week_end:
                self._draw_exam_block(exam, exam_date)

        self._draw_current_time_indicator()

    def _process_and_draw_entry(self, entry):
        subject = self.subjects_cache.get(entry["subject_id"])
        if not subject: return

        day_idx = entry["day_of_week"]
        current_entry_date = self.current_week_monday + timedelta(days=day_idx)
        current_entry_date_str = str(current_entry_date)

        s_start = subject.get("start_datetime")
        s_end = subject.get("end_datetime")

        if s_start:
            try:
                dt_start = datetime.strptime(s_start.split()[0], "%Y-%m-%d").date()
                if current_entry_date < dt_start: return
            except:
                pass

        if s_end:
            try:
                dt_end = datetime.strptime(s_end.split()[0], "%Y-%m-%d").date()
                if current_entry_date > dt_end: return
            except:
                pass

        if (entry["id"], current_entry_date_str) in self.cancellations:
            return

        self._draw_block(subject, entry, current_entry_date_str)

    def _draw_block(self, subject, entry, date_str):
        try:
            start_h, start_m = map(int, entry["start_time"].split(":"))
            end_h, end_m = map(int, entry["end_time"].split(":"))
        except:
            return

        start_val = start_h + start_m / 60.0
        end_val = end_h + end_m / 60.0
        duration = end_val - start_val

        y_pos = (start_val - START_HOUR) * PX_PER_HOUR
        height = duration * PX_PER_HOUR
        day_idx = entry["day_of_week"]

        color = subject["color"]
        text = f"{subject['short_name']}\n{entry.get('type', '')}\n{entry.get('room', '')}"

        container = ctk.CTkFrame(self.grid_area, fg_color=color, corner_radius=6, height=int(height - 2))
        container.is_block = True

        white_border = ctk.CTkFrame(container, fg_color="white", corner_radius=5)
        white_border.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        lbl = ctk.CTkLabel(white_border, text=text,
                           fg_color=("white", "#2b2b2b"),
                           text_color=("black", "white"),
                           font=("Arial", 11),
                           wraplength=85)
        lbl.pack(expand=True, fill="both", padx=4, pady=4)

        for widget in [container, white_border, lbl]:
            widget.bind("<Button-3>", lambda e: self.show_context_menu(e, entry["id"], date_str))
            if self._tk_ws() == "aqua":
                widget.bind("<Button-2>", lambda e: self.show_context_menu(e, entry["id"], date_str))

        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)
        container.place(relx=rel_x, y=y_pos, relwidth=rel_w - 0.005)

    def _draw_exam_block(self, exam, exam_date):
        subject = self.subjects_cache.get(exam["subject_id"])
        if not subject: return

        time_str = exam.get("time") or "08:00"

        try:
            start_h, start_m = map(int, time_str.split(":"))
        except (ValueError, TypeError):
            return

        start_val = start_h + start_m / 60.0
        duration = EXAM_DURATION_HOURS

        y_pos = (start_val - START_HOUR) * PX_PER_HOUR
        height = duration * PX_PER_HOUR
        day_idx = exam_date.weekday()

        color = "#e74c3c"
        text = f"{subject['short_name']}\n{exam['title']}"

        container = ctk.CTkFrame(self.grid_area, fg_color=color, corner_radius=6, height=int(height - 2))
        container.is_block = True

        white_border = ctk.CTkFrame(container, fg_color="white", corner_radius=5)
        white_border.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        lbl = ctk.CTkLabel(white_border, text=text,
                           fg_color=("white", "#2b2b2b"),
                           text_color=("black", "white"),
                           font=("Arial", 11, "bold"),
                           wraplength=85)
        lbl.pack(expand=True, fill="both", padx=4, pady=4)

        # ZMIANA: Obsługa edycji egzaminu
        for widget in [container, white_border, lbl]:
             widget.bind("<Button-3>", lambda e: self.on_exam_right_click(e, exam["id"]))
             if self._tk_ws() == "aqua":
                 widget.bind("<Button-2>", lambda e: self.on_exam_right_click(e, exam["id"]))

        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)
        container.place(relx=rel_x, y=y_pos, relwidth=rel_w - 0.005)
        container.lift()

    def show_context_menu(self, event, entry_id, date_str):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.txt.get("ctx_cancel_class", "Cancel class (this week only)"),
                         command=lambda: self.cancel_class_instance(entry_id, date_str))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ZMIANA: Nowa funkcja do menu kontekstowego egzaminu
    def on_exam_right_click(self, event, exam_id):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.txt.get("btn_edit", "Edit"),
                         command=lambda: self.on_exam_edit_click(exam_id))

        try:
             menu.tk_popup(event.x_root, event.y_root)
        finally:
             menu.grab_release()

    def on_exam_edit_click(self, exam_id):
        if not self.drawer: return
        exam = self.storage.get_exam(exam_id)
        if not exam: return

        self.drawer.set_content(EditExamPanel,
                                txt=self.txt,
                                btn_style=self.btn_style,
                                exam_data=exam,
                                storage=self.storage,
                                callback=self.refresh_schedule,
                                close_callback=self.drawer.close_panel)

    # ZMIANA: Nowa funkcja obsługi PPM na pustej siatce
    def on_grid_right_click(self, event):
        # Obliczenia pozycji
        width = self.grid_area.winfo_width()
        if width <= 0: return # Jeszcze nie wyrenderowane

        # Margines to 0.06 relatywnej szerokości, reszta to 7 dni
        margin_px = width * 0.06
        day_width_px = (width - margin_px) / 7

        click_x = event.x
        click_y = event.y

        if click_x < margin_px: return # Kliknięto na oś czasu

        day_idx = int((click_x - margin_px) // day_width_px)
        if day_idx < 0: day_idx = 0
        if day_idx > 6: day_idx = 6

        clicked_date = self.current_week_monday + timedelta(days=day_idx)
        clicked_date_str = str(clicked_date)

        # Obliczanie godziny i ZAOKRĄGLANIE DO 5 MIN
        hour_val = START_HOUR + (click_y / PX_PER_HOUR)
        clicked_hour = int(hour_val)
        raw_minute = int((hour_val - clicked_hour) * 60)

        # Zaokrąglanie
        remainder = raw_minute % 5
        if remainder < 3:
            final_minute = raw_minute - remainder
        else:
            final_minute = raw_minute + (5 - remainder)

        # Obsługa przejścia godziny
        if final_minute == 60:
            final_minute = 0
            clicked_hour += 1

        if clicked_hour > 23: clicked_hour = 23

        time_str = f"{clicked_hour:02d}:{final_minute:02d}"

        menu = tk.Menu(self, tearoff=0)

        # 1. Dodaj egzamin
        label_add = f"{self.txt.get('ctx_add_exam_at', 'Add Exam Here')} ({clicked_date.strftime('%Y-%m-%d')} {time_str})"
        menu.add_command(label=label_add, command=lambda: self.open_add_exam_at(clicked_date, time_str))

        menu.add_separator()

        # 2. Dni wolne - przełączanie (Toggle)
        is_blocked = clicked_date_str in self.storage.get_blocked_dates()

        if is_blocked:
             menu.add_command(label=f"{self.txt.get('ctx_unblock_day', 'Restore Day')}: {clicked_date_str}",
                              command=lambda: self.toggle_day_block(clicked_date_str, False))
        else:
             menu.add_command(label=f"{self.txt.get('ctx_block_day', 'Mark as Day Off')}: {clicked_date_str}",
                              command=lambda: self.toggle_day_block(clicked_date_str, True))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def toggle_day_block(self, date_str, block):
        if block:
            self.storage.add_blocked_date(date_str)
            # Aktualizacja statystyk (dodanie dnia wolnego)
            stats = self.storage.get_global_stats()
            curr = stats.get("days_off", 0)
            self.storage.update_global_stat("days_off", curr + 1)
        else:
            self.storage.remove_blocked_date(date_str)

        self.refresh_schedule()

    def open_add_exam_at(self, date_obj, time_str):
        if not self.drawer: return
        self.drawer.set_content(AddExamPanel,
                                txt=self.txt,
                                btn_style=self.btn_style,
                                storage=self.storage,
                                callback=self.refresh_schedule, # Odśwież harmonogram po dodaniu
                                close_callback=self.drawer.close_panel,
                                initial_date=date_obj,
                                initial_time=time_str)

    def open_blocked_days(self):
        if not self.drawer: return
        self.drawer.set_content(BlockedDaysPanel,
                                txt=self.txt,
                                btn_style=self.btn_style,
                                callback=self.refresh_schedule,
                                refresh_callback=self.refresh_schedule,
                                storage=self.storage,
                                close_callback=self.drawer.close_panel)

    def cancel_class_instance(self, entry_id, date_str):
        if messagebox.askyesno(self.txt["msg_confirm"],
                               self.txt.get("msg_confirm_cancel", "Remove this class instance?")):
            self.storage.add_schedule_cancellation(entry_id, date_str)
            self.refresh_schedule()

    def _tk_ws(self):
        try:
            return self.winfo_toplevel().tk.call('tk', 'windowingsystem')
        except:
            return ""

    def _draw_current_time_indicator(self):
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        if self.current_week_monday != week_start:
            return

        now = datetime.now()
        day_idx = now.weekday()
        hour = now.hour
        minute = now.minute

        current_val = hour + minute / 60.0

        if current_val < START_HOUR or current_val > END_HOUR:
            return

        y_pos = (current_val - START_HOUR) * PX_PER_HOUR
        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)

        line = ctk.CTkFrame(self.grid_area, height=2, fg_color="#e74c3c")
        line.is_marker = True
        line.place(relx=rel_x, y=y_pos, relwidth=rel_w)
        line.lift()

        dot = ctk.CTkFrame(self.grid_area, width=8, height=8, corner_radius=4, fg_color="#e74c3c")
        dot.is_marker = True
        dot.place(x=42, y=y_pos - 3)
        dot.lift()