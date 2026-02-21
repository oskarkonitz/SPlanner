import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime, timedelta, date
from gui.dialogs.subjects_manager import SubjectsManagerPanel
from gui.dialogs.add_exam import AddExamPanel
from gui.dialogs.blocked_days import BlockedDaysPanel
from gui.dialogs.edit import EditExamPanel
from gui.dialogs.custom_events import ManageListsPanel, AddCustomEventPanel, ManageEventsPanel

# Stałe konfiguracyjne
START_HOUR = 7  # Początek osi czasu (7:00)
END_HOUR = 23  # Koniec osi czasu (22:00)
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
        self.drawer = drawer

        self.current_semester_id = None
        self.semesters = []
        self.subjects_cache = {}
        self.cancellations = set()

        # Zmienne do zaawansowanego filtrowania (Puste = pokazuj wszystko)
        self.selected_semesters = set()
        self.selected_lists = set()
        self.filter_vars = {}
        self.event_lists = []

        # Oblicz start bieżącego tygodnia
        today = date.today()
        self.current_week_monday = today - timedelta(days=today.weekday())

        # --- GÓRNY PASEK (PRZYCISKI) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(self.top_frame, text=self.txt.get("lbl_schedule", "Schedule"),
                     font=("Arial", 20, "bold")).pack(side="left", padx=5)

        self.btn_filters = ctk.CTkButton(self.top_frame, text="Filters", width=90,
                                         fg_color="transparent", border_width=1, border_color="gray",
                                         text_color=("gray10", "gray90"),
                                         command=self.open_filters_menu)
        self.btn_filters.pack(side="left", padx=10)

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

        self.btn_more = ctk.CTkButton(self.top_frame, text="•••", width=40, height=30,
                                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                                      command=self.open_more_menu)
        self.btn_more.pack(side="right", padx=5)

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

            if day_date == today:
                lbl.configure(font=("Arial", 12, "bold", "underline"), text_color="violet")
            else:
                lbl.configure(font=("Arial", 12, "bold"), text_color=("black", "white"))

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
        self.event_lists = self.storage.get_event_lists()
        self.refresh_schedule()

    # ==========================================
    # MENU I FILTROWANIE
    # ==========================================
    def open_filters_menu(self):
        self.load_data()
        menu = tk.Menu(self, tearoff=0, font=("Arial", 11))

        menu.add_command(label="--- SEMESTERS ---", state="disabled")
        for sem in self.semesters:
            v_name = f"sem_{sem['id']}"
            if v_name not in self.filter_vars:
                self.filter_vars[v_name] = tk.BooleanVar(value=(sem['id'] in self.selected_semesters))

            def toggle_sem(s_id=sem['id'], var_name=v_name):
                if self.filter_vars[var_name].get():
                    self.selected_semesters.add(s_id)
                else:
                    self.selected_semesters.discard(s_id)
                self.refresh_schedule()

            menu.add_checkbutton(label=sem['name'], variable=self.filter_vars[v_name], command=toggle_sem)

        menu.add_command(label="--- CATEGORIES ---", state="disabled")
        for lst in self.event_lists:
            v_name = f"lst_{lst['id']}"
            if v_name not in self.filter_vars:
                self.filter_vars[v_name] = tk.BooleanVar(value=(lst['id'] in self.selected_lists))

            def toggle_lst(l_id=lst['id'], var_name=v_name):
                if self.filter_vars[var_name].get():
                    self.selected_lists.add(l_id)
                else:
                    self.selected_lists.discard(l_id)
                self.refresh_schedule()

            menu.add_checkbutton(label=lst['name'], variable=self.filter_vars[v_name], command=toggle_lst)

        x = self.btn_filters.winfo_rootx()
        y = self.btn_filters.winfo_rooty() + self.btn_filters.winfo_height()
        menu.tk_popup(x, y)

    def open_more_menu(self):
        menu = tk.Menu(self, tearoff=0, font=("Arial", 11))
        menu.add_command(label="Add Event", command=self.open_add_event)
        menu.add_command(label="Manage Events", command=self.open_manage_events)
        menu.add_command(label="Manage Lists", command=self.open_manage_lists)
        menu.add_separator()
        menu.add_command(label=self.txt.get("btn_edit_subjects", "Edit Subjects"), command=self.open_subjects_manager)
        menu.add_command(label="Blocked Days", command=self.open_blocked_days)

        x = self.btn_more.winfo_rootx() - 100
        y = self.btn_more.winfo_rooty() + self.btn_more.winfo_height()
        menu.tk_popup(x, y)

    # ==========================================
    # OTWIERANIE PANELI W SZUFLADZIE
    # ==========================================
    def open_add_event(self):
        if self.drawer:
            self.drawer.set_content(AddCustomEventPanel, txt=self.txt, btn_style=self.btn_style, storage=self.storage,
                                    refresh_callback=self.full_refresh, close_callback=self.drawer.close_panel)

    def open_manage_events(self):
        if self.drawer:
            self.drawer.set_content(ManageEventsPanel, txt=self.txt, btn_style=self.btn_style, storage=self.storage,
                                    refresh_callback=self.full_refresh, close_callback=self.drawer.close_panel,
                                    drawer=self.drawer)

    def open_manage_lists(self):
        if self.drawer:
            self.drawer.set_content(ManageListsPanel, txt=self.txt, btn_style=self.btn_style, storage=self.storage,
                                    refresh_callback=self.full_refresh, close_callback=self.drawer.close_panel)

    def open_subjects_manager(self):
        if self.subjects_callback:
            self.subjects_callback()
        else:
            if self.drawer:
                self.drawer.set_content(SubjectsManagerPanel, txt=self.txt, btn_style=self.btn_style,
                                        storage=self.storage, refresh_callback=self.load_data,
                                        close_callback=self.drawer.close_panel, drawer=self.drawer)
            else:
                top = ctk.CTkToplevel(self)
                top.title(self.txt.get("win_subj_man_title", "Subjects"))
                top.geometry("1000x700")
                SubjectsManagerPanel(top, self.txt, self.btn_style, self.storage,
                                     refresh_callback=self.load_data).pack(fill="both", expand=True)

    def open_blocked_days(self):
        if not self.drawer: return
        self.drawer.set_content(BlockedDaysPanel,
                                txt=self.txt,
                                btn_style=self.btn_style,
                                callback=self.refresh_schedule,
                                refresh_callback=self.refresh_schedule,
                                storage=self.storage,
                                close_callback=self.drawer.close_panel)

    def open_add_exam_at(self, date_obj, time_str):
        if not self.drawer: return
        self.drawer.set_content(AddExamPanel,
                                txt=self.txt,
                                btn_style=self.btn_style,
                                storage=self.storage,
                                callback=self.refresh_schedule,
                                close_callback=self.drawer.close_panel,
                                initial_date=date_obj,
                                initial_time=time_str)

    def full_refresh(self):
        self.load_data()
        self.refresh_schedule()

    # ==========================================
    # LOGIKA HARMONOGRAMU
    # ==========================================
    def refresh_schedule(self):
        self.update_week_label()

        for widget in self.grid_area.winfo_children():
            if isinstance(widget, ctk.CTkButton) or \
                    (isinstance(widget, ctk.CTkFrame) and (
                            getattr(widget, "is_marker", False) or getattr(widget, "is_block", False))):
                widget.destroy()

        raw_subjects = self.storage.get_subjects(None)

        self.subjects_cache = {s["id"]: dict(s) for s in raw_subjects}
        semester_subj_ids = set(self.subjects_cache.keys())

        raw_cancels = self.storage.get_schedule_cancellations()
        self.cancellations = {(c["entry_id"], c["date"]) for c in raw_cancels}

        # 1. RYSOWANIE ZAJĘĆ (PLAN)
        all_schedule = [dict(x) for x in self.storage.get_schedule()]
        for entry in all_schedule:
            sub = self.subjects_cache.get(entry["subject_id"])
            if sub and self.selected_semesters and sub.get("semester_id") not in self.selected_semesters:
                continue
            self._process_and_draw_entry(entry)

        # 2. RYSOWANIE EGZAMINÓW
        all_exams = [dict(e) for e in self.storage.get_exams()]
        week_end = self.current_week_monday + timedelta(days=6)

        for exam in all_exams:
            if exam.get("subject_id") not in semester_subj_ids:
                continue

            sub = self.subjects_cache.get(exam.get("subject_id"))
            if sub and self.selected_semesters and sub.get("semester_id") not in self.selected_semesters:
                continue

            try:
                exam_date = datetime.strptime(exam["date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            if self.current_week_monday <= exam_date <= week_end:
                self._draw_exam_block(exam, exam_date)

        # 3. RYSOWANIE WYDARZEŃ Z GRAFIKU (CUSTOM EVENTS) - Zmodyfikowane pod wydarzenia wielodniowe
        custom_events = self.storage.get_custom_events()
        for ev in custom_events:
            if self.selected_lists and ev.get("list_id") not in self.selected_lists:
                continue

            is_rec = ev.get("is_recurring", False)

            if not is_rec:
                start_date_str = ev.get("date") or ev.get("start_date")
                end_date_str = ev.get("end_date") or start_date_str
                if start_date_str:
                    try:
                        s_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                        e_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

                        # Iterujemy po wszystkich dniach trwania wydarzenia
                        curr_date = s_date
                        while curr_date <= e_date:
                            if self.current_week_monday <= curr_date <= week_end:
                                day_idx = curr_date.weekday()
                                self._draw_custom_event_block(ev, str(curr_date), day_idx)
                            curr_date += timedelta(days=1)
                    except:
                        pass
            else:
                ev_day = ev.get("day_of_week")
                if ev_day is not None and 0 <= ev_day <= 6:
                    target_date = self.current_week_monday + timedelta(days=ev_day)
                    target_date_str = str(target_date)

                    valid = True
                    s_date = ev.get("start_date")
                    e_date = ev.get("end_date")

                    if s_date and target_date_str < s_date: valid = False
                    if e_date and target_date_str > e_date: valid = False

                    if valid:
                        self._draw_custom_event_block(ev, target_date_str, ev_day)

        self._draw_current_time_indicator()

    # --- HELPERS DO KOLORÓW (SYMULACJA PRZEZROCZYSTOŚCI) ---
    def _hex_to_rgb(self, hex_color):
        if not hex_color or not hex_color.startswith("#"): return (128, 128, 128)
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))

    def _rgb_to_hex(self, rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    def _blend_colors(self, hex1, hex2, alpha):
        r1, g1, b1 = self._hex_to_rgb(hex1)
        r2, g2, b2 = self._hex_to_rgb(hex2)
        r = int(r1 * alpha + r2 * (1 - alpha))
        g = int(g1 * alpha + g2 * (1 - alpha))
        b = int(b1 * alpha + b2 * (1 - alpha))
        return self._rgb_to_hex((r, g, b))

    def _get_tinted_color(self, color):
        l = self._blend_colors(color, "#ffffff", 0.25)
        d = self._blend_colors(color, "#2b2b2b", 0.25)
        return (l, d)

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

        # --- LOGIKA TEKSTU (USTAWIENIA) ---
        settings = self.storage.get_settings()
        show_full_name = settings.get("schedule_use_full_name", False)
        show_times = settings.get("schedule_show_times", False)
        show_room = settings.get("schedule_show_room", True)

        lines = []
        # 1. Nazwa
        subj_text = subject['name'] if show_full_name else subject['short_name']
        lines.append(subj_text)

        # 2. Czas (np. 08:00 - 09:30)
        if show_times:
            lines.append(f"{entry['start_time']} - {entry['end_time']}")

        # 3. Typ zajęć
        if entry.get('type'):
            lines.append(entry['type'])

        # 4. Sala
        if show_room and entry.get('room'):
            lines.append(entry['room'])

        text = "\n".join(lines)
        # ----------------------------------

        tint_color = self._get_tinted_color(color)

        container = ctk.CTkFrame(
            self.grid_area,
            fg_color=tint_color,
            border_color=color,
            border_width=2,
            corner_radius=6,
            height=int(height - 2)
        )
        container.is_block = True

        white_border = ctk.CTkFrame(container, fg_color="transparent", corner_radius=5)
        white_border.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        lbl = ctk.CTkLabel(white_border, text=text,
                           fg_color="transparent",
                           text_color=("black", "white"),
                           font=("Arial", 11),
                           wraplength=85)
        lbl.pack(expand=True, fill="both", padx=2, pady=2)

        for widget in [container, white_border, lbl]:
            widget.bind("<Button-3>", lambda e: self.show_context_menu(e, entry["id"], date_str))
            if self._tk_ws() == "aqua":
                widget.bind("<Button-2>", lambda e: self.show_context_menu(e, entry["id"], date_str))

        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)
        container.place(relx=rel_x, y=y_pos, relwidth=rel_w - 0.005)
        container.lift()

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

        # --- LOGIKA TEKSTU DLA EGZAMINÓW ---
        settings = self.storage.get_settings()
        show_full_name = settings.get("schedule_use_full_name", False)

        subj_text = subject['name'] if show_full_name else subject['short_name']
        text = f"{subj_text}\n\n{exam['title']}"
        # -----------------------------------

        tint_color = self._get_tinted_color(color)

        container = ctk.CTkFrame(
            self.grid_area,
            fg_color=tint_color,
            border_color=color,
            border_width=2,
            corner_radius=6,
            height=int(height - 2)
        )
        container.is_block = True

        white_border = ctk.CTkFrame(container, fg_color="transparent", corner_radius=5)
        white_border.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        lbl = ctk.CTkLabel(white_border, text=text,
                           fg_color="transparent",
                           text_color=("black", "white"),
                           font=("Arial", 11, "bold"),
                           wraplength=85)
        lbl.pack(expand=True, fill="both", padx=2, pady=2)

        for widget in [container, white_border, lbl]:
            widget.bind("<Button-3>", lambda e: self.on_exam_right_click(e, exam["id"]))
            if self._tk_ws() == "aqua":
                widget.bind("<Button-2>", lambda e: self.on_exam_right_click(e, exam["id"]))

        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)
        container.place(relx=rel_x, y=y_pos, relwidth=rel_w - 0.005)
        container.lift()

    def _draw_custom_event_block(self, ev, date_str, day_idx):
        try:
            ev_start_date = ev.get("date") or ev.get("start_date")
            ev_end_date = ev.get("end_date") or ev_start_date

            start_time_str = ev.get("start_time", "00:00")
            end_time_str = ev.get("end_time", "00:00")

            start_h, start_m = map(int, start_time_str.split(":"))
            end_h, end_m = map(int, end_time_str.split(":"))

            event_start_val = start_h + start_m / 60.0
            event_end_val = end_h + end_m / 60.0
        except Exception:
            return

        is_start_day = (date_str == ev_start_date)
        is_end_day = (date_str == ev_end_date)
        is_middle_day = (ev_start_date < date_str < ev_end_date)

        draw_start_val = float(START_HOUR)
        draw_end_val = float(END_HOUR)

        if is_start_day:
            draw_start_val = max(float(START_HOUR), event_start_val)
            if is_end_day:
                draw_end_val = min(float(END_HOUR), event_end_val)
        elif is_end_day:
            draw_end_val = min(float(END_HOUR), event_end_val)
        elif not is_middle_day:
            return

        duration = draw_end_val - draw_start_val
        if duration <= 0: return

        y_pos = (draw_start_val - START_HOUR) * PX_PER_HOUR
        height = duration * PX_PER_HOUR

        display_end = self.txt.get("label_end_of_day", "End of the day") if end_time_str in ["23:59",
                                                                                             "00:00"] else end_time_str

        if is_start_day and is_end_day:
            time_text = f"{start_time_str} - {display_end}"
        elif is_start_day:
            time_text = f"{start_time_str} -> ..."
        elif is_end_day:
            time_text = f"... -> {display_end}"
        else:
            time_text = self.txt.get("label_all_day", "Full day")

        color = ev.get("color", "#e67e22")
        text = f"{ev.get('title', 'Event')}\n{time_text}"

        tint_color = self._get_tinted_color(color)
        container = ctk.CTkFrame(self.grid_area, fg_color=tint_color, border_color=color, border_width=2,
                                 corner_radius=6, height=int(height - 2))
        container.is_block = True

        white_border = ctk.CTkFrame(container, fg_color="transparent", corner_radius=5)
        white_border.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.92, relheight=0.88)

        lbl = ctk.CTkLabel(white_border, text=text, fg_color="transparent", text_color=("black", "white"),
                           font=("Arial", 11, "bold"), wraplength=85)
        lbl.pack(expand=True, fill="both", padx=2, pady=2)

        def show_ev_menu(e, ev_data=ev):
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label=self.txt.get("btn_edit", "Edit"),
                             command=lambda: self.edit_custom_event(ev_data))
            menu.add_command(label=self.txt.get("btn_delete", "Delete"),
                             command=lambda: self.delete_custom_event(ev_data["id"]))
            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()

        for widget in [container, white_border, lbl]:
            widget.bind("<Button-3>", show_ev_menu)
            if self._tk_ws() == "aqua":
                widget.bind("<Button-2>", show_ev_menu)

        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)
        container.place(relx=rel_x, y=y_pos, relwidth=rel_w - 0.005)
        container.lift()

    def edit_custom_event(self, ev_data):
        if self.drawer:
            self.drawer.set_content(AddCustomEventPanel, txt=self.txt, btn_style=self.btn_style, storage=self.storage,
                                    refresh_callback=self.full_refresh, close_callback=self.drawer.close_panel,
                                    event_data=ev_data)

    def delete_custom_event(self, ev_id):
        if messagebox.askyesno(self.txt.get("msg_warning", "Warning"), "Delete this event?"):
            self.storage.delete_custom_event(ev_id)
            self.refresh_schedule()

    def show_context_menu(self, event, entry_id, date_str):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.txt.get("ctx_cancel_class", "Cancel class (this week only)"),
                         command=lambda: self.cancel_class_instance(entry_id, date_str))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

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

    def on_grid_right_click(self, event):
        width = self.grid_area.winfo_width()
        if width <= 0: return

        margin_px = width * 0.06
        day_width_px = (width - margin_px) / 7

        click_x = event.x
        click_y = event.y

        if click_x < margin_px: return

        day_idx = int((click_x - margin_px) // day_width_px)
        if day_idx < 0: day_idx = 0
        if day_idx > 6: day_idx = 6

        clicked_date = self.current_week_monday + timedelta(days=day_idx)
        clicked_date_str = str(clicked_date)

        hour_val = START_HOUR + (click_y / PX_PER_HOUR)
        clicked_hour = int(hour_val)
        raw_minute = int((hour_val - clicked_hour) * 60)

        remainder = raw_minute % 5
        if remainder < 3:
            final_minute = raw_minute - remainder
        else:
            final_minute = raw_minute + (5 - remainder)

        if final_minute == 60:
            final_minute = 0
            clicked_hour += 1

        if clicked_hour > 23: clicked_hour = 23

        time_str = f"{clicked_hour:02d}:{final_minute:02d}"

        menu = tk.Menu(self, tearoff=0)

        label_add = f"{self.txt.get('ctx_add_exam_at', 'Add Exam Here')} ({clicked_date.strftime('%Y-%m-%d')} {time_str})"
        menu.add_command(label=label_add, command=lambda: self.open_add_exam_at(clicked_date, time_str))

        menu.add_separator()

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
            stats = self.storage.get_global_stats()
            curr = stats.get("days_off", 0)
            self.storage.update_global_stat("days_off", curr + 1)
        else:
            self.storage.remove_blocked_date(date_str)

        self.refresh_schedule()

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