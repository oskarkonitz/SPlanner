import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime, timedelta, date
from gui.dialogs.subjects_manager import SubjectsManagerWindow

# Stałe konfiguracyjne
START_HOUR = 7  # Początek osi czasu (7:00)
END_HOUR = 22  # Koniec osi czasu (22:00)
PX_PER_HOUR = 60  # Wysokość jednej godziny w pikselach
EXAM_DURATION_HOURS = 1.5  # Domyślny czas trwania kafelka egzaminu (dla wizualizacji)
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SchedulePanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage):
        # 1. GŁÓWNY KONTENER
        super().__init__(parent, fg_color="transparent")

        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage

        self.current_semester_id = None
        self.semesters = []
        self.subjects_cache = {}
        self.cancellations = set()  # Zbiór (entry_id, date_str) odwołanych zajęć

        # Oblicz start bieżącego tygodnia (Poniedziałek)
        today = date.today()
        self.current_week_monday = today - timedelta(days=today.weekday())

        # --- GÓRNY PASEK (PRZYCISKI) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", pady=(0, 5))

        # Tytuł
        ctk.CTkLabel(self.top_frame, text=self.txt.get("lbl_schedule", "Schedule"),
                     font=("Arial", 20, "bold")).pack(side="left", padx=5)

        # Wybór Semestru
        self.combo_sem = ctk.CTkComboBox(self.top_frame, width=180, command=self.on_semester_change)
        self.combo_sem.pack(side="left", padx=10)

        # --- NAWIGACJA TYGODNIOWA ---
        nav_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        nav_frame.pack(side="left", padx=20)

        # Przycisk "Poprzedni tydzień"
        ctk.CTkButton(nav_frame, text="<", width=30, height=28,
                      fg_color="transparent", border_width=1, border_color="gray",
                      text_color=("gray10", "gray90"),
                      command=self.prev_week).pack(side="left", padx=2)

        # Etykieta daty
        self.lbl_week_date = ctk.CTkLabel(nav_frame, text="", width=180, font=("Arial", 12, "bold"))
        self.lbl_week_date.pack(side="left", padx=5)

        # Przycisk "Następny tydzień"
        ctk.CTkButton(nav_frame, text=">", width=30, height=28,
                      fg_color="transparent", border_width=1, border_color="gray",
                      text_color=("gray10", "gray90"),
                      command=self.next_week).pack(side="left", padx=2)

        # Przycisk "Dziś"
        ctk.CTkButton(nav_frame, text=self.txt.get("btn_today", "Today"), width=60, height=28,
                      command=self.go_to_today).pack(side="left", padx=10)

        # Przycisk "Zarządzaj Przedmiotami"
        ctk.CTkButton(self.top_frame, text=self.txt.get("btn_edit_subjects", "Edit Subjects"),
                      command=self.open_subjects_manager,
                      width=120, height=30,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=5)

        # --- BIAŁA RAMKA (BORDER FRAME) ---
        self.border_frame = ctk.CTkFrame(self, fg_color="transparent",
                                         border_width=1,
                                         border_color=("gray70", "white"),
                                         corner_radius=8)
        self.border_frame.pack(fill="both", expand=True)

        # --- NAGŁÓWKI DNI TYGODNIA ---
        self.header_frame = ctk.CTkFrame(self.border_frame, height=30, corner_radius=0, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=3, pady=(3, 0))

        # Pusta przestrzeń nad godzinami
        ctk.CTkFrame(self.header_frame, width=50, height=30, fg_color="transparent").pack(side="left")

        # Etykiety dni (zostaną zaktualizowane w refresh)
        self.day_labels = []
        for i in range(7):
            lbl = ctk.CTkLabel(self.header_frame, text="", font=("Arial", 12, "bold"))
            lbl.pack(side="left", expand=True, fill="x")
            self.day_labels.append(lbl)

        # --- OBSZAR PRZEWIJANY (Wewnątrz border_frame) ---
        # Kolor tła planu: ("white", "#2b2b2b")
        self.scroll_frame = ctk.CTkScrollableFrame(self.border_frame, corner_radius=6, fg_color=("white", "#2b2b2b"))
        self.scroll_frame.pack(fill="both", expand=True, padx=3, pady=3)

        # Canvas na bloczki
        total_height = (END_HOUR - START_HOUR) * PX_PER_HOUR + 50
        self.grid_area = ctk.CTkFrame(self.scroll_frame, height=total_height, fg_color="transparent")
        self.grid_area.pack(fill="x", expand=True)

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

    # --- NAWIGACJA CZASOWA ---
    def update_week_label(self):
        monday = self.current_week_monday
        sunday = monday + timedelta(days=6)
        txt = f"{monday.strftime('%d.%m')} - {sunday.strftime('%d.%m.%Y')}"
        self.lbl_week_date.configure(text=txt)

        # Aktualizacja nagłówków dni (np. "Pon 12.02")
        for i, lbl in enumerate(self.day_labels):
            day_date = monday + timedelta(days=i)
            day_name = self.txt.get(f"day_{DAYS[i].lower()}", DAYS[i])
            lbl.configure(text=f"{day_name} {day_date.strftime('%d.%m')}")

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

    # --- ŁADOWANIE DANYCH ---
    def load_data(self):
        self.semesters = [dict(s) for s in self.storage.get_semesters()]
        # Sortujemy semestry, aby aktualny był na szczycie (dla domyślnego wyboru)
        self.semesters.sort(key=lambda x: not x["is_current"])

        # Lista wartości do ComboBox: "All" + nazwy semestrów
        all_label = self.txt.get("val_all", "All")
        sem_names = [s["name"] for s in self.semesters]
        values = [all_label] + sem_names

        self.combo_sem.configure(values=values)

        # Logika wyboru domyślnego
        if self.semesters:
            if not self.current_semester_id:
                # Domyślnie wybieramy pierwszy semestr (aktualny dzięki sortowaniu)
                self.current_semester_id = self.semesters[0]["id"]
                self.combo_sem.set(self.semesters[0]["name"])
            elif self.current_semester_id == "ALL":
                self.combo_sem.set(all_label)
            else:
                # Próbujemy znaleźć nazwę dla obecnego ID
                current_name = next((s["name"] for s in self.semesters if s["id"] == self.current_semester_id), None)
                if current_name:
                    self.combo_sem.set(current_name)
                else:
                    # Fallback jeśli ID nie istnieje (np. po usunięciu)
                    self.current_semester_id = self.semesters[0]["id"]
                    self.combo_sem.set(self.semesters[0]["name"])
        else:
            # Brak semestrów - tylko opcja All (choć i tak pusto)
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
        SubjectsManagerWindow(self.winfo_toplevel(), self.txt, self.btn_style, self.storage,
                              refresh_callback=self.load_data)

    def refresh_schedule(self):
        # 1. UI Updates
        self.update_week_label()

        # Wyczyść stare bloczki (zabezpieczamy się usuwając tylko elementy harmonogramu i markery)
        for widget in self.grid_area.winfo_children():
            if isinstance(widget, ctk.CTkButton) or \
                    (isinstance(widget, ctk.CTkFrame) and (
                            getattr(widget, "is_marker", False) or getattr(widget, "is_block", False))):
                widget.destroy()

        if not self.current_semester_id: return

        # 2. Pobierz przedmioty
        if self.current_semester_id == "ALL":
            # Pobieramy przedmioty ze WSZYSTKICH semestrów
            raw_subjects = self.storage.get_subjects(None)
        else:
            # Pobieramy tylko dla konkretnego
            raw_subjects = self.storage.get_subjects(self.current_semester_id)

        self.subjects_cache = {s["id"]: dict(s) for s in raw_subjects}
        semester_subj_ids = set(self.subjects_cache.keys())

        # 3. Pobierz Odwołania (Exceptions)
        raw_cancels = self.storage.get_schedule_cancellations()
        self.cancellations = {(c["entry_id"], c["date"]) for c in raw_cancels}

        # 4. Pobierz wpisy harmonogramu (Zajęcia cykliczne)
        all_schedule = [dict(x) for x in self.storage.get_schedule()]

        # 5. Rysowanie ZAJĘĆ CYKLICZNYCH
        for entry in all_schedule:
            self._process_and_draw_entry(entry)

        # 6. Rysowanie EGZAMINÓW (Na wierzchu - hierarchia)
        all_exams = [dict(e) for e in self.storage.get_exams()]
        week_end = self.current_week_monday + timedelta(days=6)

        for exam in all_exams:
            # Pomiń egzaminy przedmiotów, których nie ma w cache (filtrowanie po semestrze)
            if exam.get("subject_id") not in semester_subj_ids:
                continue

            try:
                exam_date = datetime.strptime(exam["date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                continue

            # Sprawdź czy egzamin jest w wyświetlanym tygodniu
            if self.current_week_monday <= exam_date <= week_end:
                self._draw_exam_block(exam, exam_date)

        self._draw_current_time_indicator()

    def _process_and_draw_entry(self, entry):
        # Sprawdź czy przedmiot należy do obecnego widoku (semestr lub all)
        subject = self.subjects_cache.get(entry["subject_id"])
        if not subject: return

        # 1. FILTROWANIE PO DATACH PRZEDMIOTU
        # Oblicz datę tego zajęcia w bieżącym widoku tygodnia
        day_idx = entry["day_of_week"]
        current_entry_date = self.current_week_monday + timedelta(days=day_idx)
        current_entry_date_str = str(current_entry_date)

        # Sprawdź start/end przedmiotu (jeśli ustawione)
        s_start = subject.get("start_datetime")
        s_end = subject.get("end_datetime")

        if s_start:
            try:
                dt_start = datetime.strptime(s_start.split()[0], "%Y-%m-%d").date()
                if current_entry_date < dt_start: return  # Jeszcze się nie zaczęło
            except:
                pass

        if s_end:
            try:
                dt_end = datetime.strptime(s_end.split()[0], "%Y-%m-%d").date()
                if current_entry_date > dt_end: return  # Już się skończyło
            except:
                pass

        # 2. SPRAWDŹ CZY NIE ODWOŁANE (EXCEPTIONS)
        if (entry["id"], current_entry_date_str) in self.cancellations:
            return  # Odwołane w tym tygodniu

        # 3. RYSUJ
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

        # --- STYL KAFELKA ---
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

        # Bindowanie PPM
        for widget in [container, white_border, lbl]:
            widget.bind("<Button-3>", lambda e: self.show_context_menu(e, entry["id"], date_str))
            if self._tk_ws() == "aqua":
                widget.bind("<Button-2>", lambda e: self.show_context_menu(e, entry["id"], date_str))

        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)
        container.place(relx=rel_x, y=y_pos, relwidth=rel_w - 0.005)

    def _draw_exam_block(self, exam, exam_date):
        """Rysuje kafelek egzaminu (czerwony, na wierzchu)."""
        subject = self.subjects_cache.get(exam["subject_id"])
        if not subject: return

        # FIX: Jeśli brakuje czasu lub jest None, ustaw domyślnie 08:00
        time_str = exam.get("time") or "08:00"

        try:
            start_h, start_m = map(int, time_str.split(":"))
        except (ValueError, TypeError):
            return

        start_val = start_h + start_m / 60.0
        duration = EXAM_DURATION_HOURS

        y_pos = (start_val - START_HOUR) * PX_PER_HOUR
        height = duration * PX_PER_HOUR
        day_idx = exam_date.weekday()  # 0=Mon, 6=Sun

        color = "#e74c3c"
        text = f"{subject['short_name']}\n{exam['title']}"

        # --- STYL KAFELKA EGZAMINU ---
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

        rel_w = (1.0 - 0.06) / 7
        rel_x = 0.06 + (day_idx * rel_w)
        container.place(relx=rel_x, y=y_pos, relwidth=rel_w - 0.005)

        # Podnieś egzamin na wierzch (żeby przykrył zwykłe zajęcia)
        container.lift()

    def show_context_menu(self, event, entry_id, date_str):
        """Menu kontekstowe do usuwania zajęć."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.txt.get("ctx_cancel_class", "Cancel class (this week only)"),
                         command=lambda: self.cancel_class_instance(entry_id, date_str))

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def cancel_class_instance(self, entry_id, date_str):
        if messagebox.askyesno(self.txt["msg_confirm"],
                               self.txt.get("msg_confirm_cancel", "Remove this class instance?")):
            self.storage.add_schedule_cancellation(entry_id, date_str)
            self.refresh_schedule()

    def _tk_ws(self):
        # FIX: Pobieramy windowingsystem z toplevel (bezpieczniej niż winfo_screen)
        try:
            return self.winfo_toplevel().tk.call('tk', 'windowingsystem')
        except:
            return ""

    def _draw_current_time_indicator(self):
        # Rysuj linię tylko jeśli obecny tydzień to "TEN" tydzień
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