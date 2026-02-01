import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date, timedelta
from core.storage import save
from core.planner import plan, date_format
from gui.windows.add_exam import AddExamWindow
from gui.windows.archive import ArchiveWindow
from gui.windows.edit import select_edit_item, EditExamWindow, EditTopicWindow
# NoteWindow nie jest już używane, ale import zostawiamy dla kompatybilności
from gui.windows.note import NoteWindow


# --- KLASA PANELU BOCZNEGO (DRAWER) ---
class NoteDrawer(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, save_callback):
        super().__init__(parent, corner_radius=0, fg_color=("gray90", "gray20"))
        self.txt = txt
        self.save_callback = save_callback
        self.current_item_data = None
        self.is_open = False

        # ID procesu animacji
        self.animation_id = None

        # Pozycja startowa (poza ekranem z prawej strony)
        self.target_x = 1.05
        self.place(relx=self.target_x, rely=0, relwidth=0.3, relheight=1.0)

        # --- UI PANELU ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=10)

        title_text = self.txt.get("drawer_title", "Notatka")
        self.lbl_title = ctk.CTkLabel(self.header_frame, text=title_text, font=("Arial", 16, "bold"), anchor="w")
        self.lbl_title.pack(side="left", fill="x", expand=True)

        self.btn_close = ctk.CTkButton(self.header_frame, text="✕", width=30, height=30,
                                       fg_color="transparent", text_color="gray", hover_color=("gray80", "gray30"),
                                       command=self.close_panel)
        self.btn_close.pack(side="right")

        self.lbl_item_name = ctk.CTkLabel(self, text="...", font=("Arial", 12), text_color="gray",
                                          anchor="w", wraplength=200)
        self.lbl_item_name.pack(fill="x", padx=15, pady=(0, 10))

        self.textbox = ctk.CTkTextbox(self, font=("Arial", 13), wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=5)

        self.btn_save = ctk.CTkButton(self, text=self.txt.get("btn_save", "Zapisz"), command=self.save_note,
                                      **btn_style)
        self.btn_save.pack(pady=15, padx=10, fill="x")

    def load_note(self, item_data, item_name):
        self.stop_animation()

        self.current_item_data = item_data
        self.lbl_item_name.configure(text=item_name)
        note_content = item_data.get("note", "")

        # Czyścimy i wstawiamy (nawet jeśli puste)
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", note_content)

        # Zapobieganie "glitchowi" wizualnemu przy ponownym otwieraniu
        try:
            current_x = float(self.place_info().get('relx', self.target_x))
            if current_x > 1.0:
                self.place(relx=1.0)  # Ustaw na krawędzi przed wjazdem
        except:
            pass

        self.open_panel()

    def save_note(self):
        if self.current_item_data is not None:
            new_text = self.textbox.get("0.0", "end-1c")
            old_text = self.current_item_data.get("note", "").strip()

            is_new = (not old_text and new_text.strip() != "")

            self.current_item_data["note"] = new_text
            self.save_callback(is_new_note=is_new)

            saved_txt = self.txt.get("btn_saved", "Zapisano!")
            orig_text = self.txt.get("btn_save", "Zapisz")
            self.btn_save.configure(text=saved_txt, fg_color="#27ae60")
            self.after(1500, lambda: self.btn_save.configure(text=orig_text, fg_color="#3a3a3a"))

    def stop_animation(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None

    def open_panel(self):
        self.stop_animation()
        self.is_open = True
        self.tkraise()
        self.lift()
        self.animate(0.7)

    def close_panel(self):
        self.stop_animation()
        self.is_open = False
        self.animate(1.05)

    def animate(self, target):
        try:
            current_val = self.place_info().get('relx')
        except (TypeError, KeyError, AttributeError):
            return

        if current_val is None:
            current = self.target_x
        else:
            current = float(current_val)

        if abs(target - current) < 0.005:
            self.place(relx=target)
            self.animation_id = None
            return

        diff = target - current
        step = diff * 0.25
        if abs(step) < 0.001: step = 0.001 if diff > 0 else -0.001

        self.place(relx=current + step)
        self.animation_id = self.after(16, lambda: self.animate(target))


# --- GŁÓWNA KLASA OKNA PLANU ---
class PlanWindow:
    def __init__(self, parent, txt, data, btn_style, dashboard_callback, selection_callback):
        self.parent = parent
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback
        self.selection_callback = selection_callback
        self.win = parent

        self.dragged_item = None
        self.drag_tooltip = None

        self.table_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("data", "przedmiot", "temat")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("data", text="")
        self.tree.column("data", width=55, anchor="e", stretch=False)
        self.tree.heading("przedmiot", text=self.txt["col_subject"])
        self.tree.column("przedmiot", width=150, anchor="w")
        self.tree.heading("temat", text=self.txt["col_topic_long"])
        self.tree.column("temat", width=300, anchor="w")

        self.tree.tag_configure("exam", foreground="red", font=("Arial", 13, "bold"))
        self.tree.tag_configure("done", foreground="green", font=("Arial", 12, "bold"))
        self.tree.tag_configure("date_header", font=("Arial", 13, "bold"))
        self.tree.tag_configure("todo", font=("Arial", 13, "bold"))
        self.tree.tag_configure("normal", font=("Arial", 12, "bold"))
        self.tree.tag_configure("today", font=("Arial", 12, "bold"), foreground="violet")
        self.tree.tag_configure("red", font=("Arial", 13, "bold"), foreground="#ff007f")
        self.tree.tag_configure("orange", font=("Arial", 12, "bold"), foreground="orange")
        self.tree.tag_configure("yellow", foreground="yellow", font=("Arial", 12, "bold"))
        self.tree.tag_configure("overdue", foreground="gray", font=("Arial", 12, "italic", "bold"))
        self.tree.tag_configure("blocked", foreground="gray", font=("Arial", 12))

        scrollbar = ctk.CTkScrollbar(self.table_frame, orientation="vertical", command=self.tree.yview,
                                     fg_color="transparent", bg_color="transparent")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.on_double_click)

        self.setup_context_menus()
        if self.win.tk.call('tk', 'windowingsystem') == 'aqua':
            self.tree.bind("<Button-2>", self.show_context_menu)
            self.tree.bind("<Control-1>", self.show_context_menu)
        else:
            self.tree.bind("<Button-3>", self.show_context_menu)

        self.tree.bind("<ButtonPress-1>", self.on_drag_start, add="+")
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_drop)

        self.drawer = NoteDrawer(self.win, self.txt, self.btn_style, self.save_data_from_drawer)

        self.refresh_table()

    def setup_context_menus(self):
        self.context_menu_topic = tk.Menu(self.tree, tearoff=0)
        self.context_menu_topic.add_command(label=self.txt.get("btn_toggle_status", "Change Status"),
                                            command=self.toggle_status)
        self.context_menu_topic.add_command(label=self.txt.get("btn_edit", "Edit"), command=self.open_edit)
        self.context_menu_topic.add_separator()
        self.context_menu_topic.add_command(label=self.txt.get("menu_notes", "Notatki"),
                                            command=self.open_notes)
        self.context_menu_topic.add_command(label=self.txt.get("menu_lock", "Zablokuj/Odblokuj"),
                                            command=self.toggle_lock)
        self.context_menu_topic.add_separator()
        self.context_menu_topic.add_command(label=self.txt.get("menu_move_tomorrow", "Move to Tomorrow"),
                                            command=self.move_to_tomorrow)

        self.context_menu_exam = tk.Menu(self.tree, tearoff=0)
        self.context_menu_exam.add_command(label=self.txt.get("btn_edit", "Edytuj"),
                                           command=self.open_edit_exam_context)
        self.context_menu_exam.add_separator()
        self.context_menu_exam.add_command(label=self.txt.get("menu_notes", "Notatki"),
                                           command=self.open_notes_exam)
        self.context_menu_exam.add_command(label=self.txt.get("menu_ignore_barrier", "Ignoruj w planowaniu (Bariera)"),
                                           command=self.toggle_exam_barrier)

    def save_data_from_drawer(self, is_new_note=False):
        if is_new_note:
            if "global_stats" not in self.data: self.data["global_stats"] = {}
            curr = self.data["global_stats"].get("notes_added", 0)
            self.data["global_stats"]["notes_added"] = curr + 1

        save(self.data)
        self.refresh_table(preserve_selection=True)
        if self.dashboard_callback: self.dashboard_callback()

    # --- LOGIKA OTWIERANIA NOTATEK Z MENU ---
    def open_notes(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)
        if target_topic:
            exam = next((e for e in self.data["exams"] if e["id"] == target_topic["exam_id"]), None)
            subject_name = exam["subject"] if exam else "???"
            drawer_title = f"{subject_name}: {target_topic['name']}"
            self.drawer.load_note(target_topic, drawer_title)

    def open_notes_exam(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_exam = next((e for e in self.data["exams"] if str(e["id"]) == str(item_id)), None)
        if target_exam:
            prefix = self.txt.get("lbl_exam_prefix", "Egzamin")
            drawer_title = f"{prefix}: {target_exam['subject']}"
            self.drawer.load_note(target_exam, drawer_title)

    def refresh_table(self, only_unscheduled=False, preserve_selection=False):
        selected_id = None
        if preserve_selection:
            sel = self.tree.selection()
            if sel: selected_id = sel[0]

        for item in self.tree.get_children():
            self.tree.delete(item)

        # 1. ZALEGŁE
        self.tree.insert("", "end", values=("", "", ""))
        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= date.today()}
        overdue_topics = [
            t for t in self.data["topics"]
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < date.today()
               and t["status"] == "todo" and t["exam_id"] in active_exams_ids
        ]

        if overdue_topics:
            self.tree.insert("", "end", values=("", self.txt["tag_overdue"], ""), tags=("overdue",))
            for topic in overdue_topics:
                subj_name = self.txt["val_other"]
                for exam in self.data["exams"]:
                    if exam["id"] == topic["exam_id"]:
                        subj_name = exam["subject"]
                        break
                has_note = topic.get("note", "").strip()
                is_locked = topic.get("locked", False)
                marks = ""
                if has_note: marks += " ✎"
                if is_locked: marks += " ☒"
                self.tree.insert("", "end", iid=topic["id"],
                                 values=(marks, f"{topic['scheduled_date']}\t{subj_name}", topic["name"]),
                                 tags=("overdue",))
            self.tree.insert("", "end", values=("", "", ""))

        # 2. DATY
        all_dates = set()
        for exam in self.data["exams"]:
            if date_format(exam["date"]) >= date.today(): all_dates.add(str(exam["date"]))
        for topic in self.data["topics"]:
            if topic["scheduled_date"] and date_format(topic["scheduled_date"]) >= date.today(): all_dates.add(
                str(topic["scheduled_date"]))
        blocked_list = self.data.get("blocked_dates", [])
        if all_dates:
            for bd in blocked_list:
                if bd >= str(date.today()) and bd <= max(all_dates): all_dates.add(bd)
        sorted_dates = sorted(list(all_dates))

        # 3. GŁÓWNA PĘTLA
        for day_str in sorted_dates:
            todays_exams = [e for e in self.data["exams"] if e["date"] == day_str]
            todays_topics = [t for t in self.data["topics"] if str(t.get("scheduled_date")) == day_str]
            is_blocked = day_str in blocked_list
            has_exams = len(todays_exams) > 0

            days_left = (date_format(day_str) - date.today()).days
            display_text = ""
            tag = "normal"
            icon = "●"

            if is_blocked and not has_exams:
                display_text = self.txt.get("tag_day_off", "(Day Off)")
                tag = "blocked"
                icon = "○"
            else:
                if days_left == 0:
                    display_text = self.txt["tag_today"]
                    tag = "today"
                elif days_left == 1:
                    display_text = self.txt["tag_1_day"]
                    tag = "red"
                else:
                    display_text = self.txt["tag_x_days"].format(days=days_left)
                    if days_left <= 3:
                        tag = "orange"
                    elif days_left <= 6:
                        tag = "yellow"
                if is_blocked:
                    display_text += f" {self.txt.get('tag_day_off', '(Day Off)')}"
                    icon = "○"

            # Pobieramy nazwę dnia tygodnia z pliku językowego
            weekday_idx = date_format(day_str).weekday()
            day_name = self.txt["days_short"][weekday_idx]

            # Wstawiamy wiersz z dodanym dniem tygodnia
            self.tree.insert("", "end", iid=f"date_{day_str}",
                             values=(icon, f"{display_text} ({day_name}, {day_str})", ""),
                             tags=(tag,))

            if not is_blocked or has_exams:
                self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))
                for exam in todays_exams:
                    marks = ""
                    if exam.get("note", "").strip(): marks += " ✎"
                    if exam.get("ignore_barrier", False): marks += " ø"
                    self.tree.insert("", "end", iid=exam["id"], values=(f"{marks} │", exam["subject"], exam["title"]),
                                     tags=("exam",))

                if not is_blocked:
                    if todays_exams and todays_topics: self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))

                    for topic in todays_topics:
                        # 1. Znajdź nazwę przedmiotu i rodzica (egzamin), żeby pobrać kolor
                        subj_name = self.txt["val_other"]
                        parent_exam = None

                        for exam in self.data["exams"]:
                            if exam["id"] == topic["exam_id"]:
                                subj_name = exam["subject"]
                                parent_exam = exam
                                break

                        # 2. Logika znaczników (ikonek)
                        has_note = topic.get("note", "").strip()
                        marks = " ✎" if has_note else ""
                        if topic.get("locked", False): marks += " ☒"

                        # 3. Logika kolorów (TO ZMIENIAMY)
                        final_tags = []

                        if topic["status"] == "done":
                            final_tags.append("done")
                        else:
                            # ZMIANA TUTAJ: Sprawdzamy, czy kolor fizycznie istnieje (nie jest None i nie jest pusty)
                            if parent_exam and parent_exam.get("color"):
                                col = parent_exam["color"]
                                tag_col_name = f"theme_{parent_exam['id']}"
                                self.tree.tag_configure(tag_col_name, foreground=col, font=("Arial", 13, "bold"))
                                final_tags.append(tag_col_name)
                            else:
                                # Jeśli parent_exam["color"] to None -> wpadamy tutaj.
                                # Tag "todo" jest obsługiwany przez theme_manager i sam zmienia kolory!
                                final_tags.append("todo")

                        # 4. Wstawienie do tabeli
                        self.tree.insert("", "end", iid=topic["id"],
                                         values=(f"{marks} │", subj_name, topic["name"]),
                                         tags=tuple(final_tags))
                self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))
            self.tree.insert("", "end", values=("", "", ""))

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.see(selected_id)

    # --- ZMIANA ZAZNACZENIA (POPRAWIONA LOGIKA) ---
    def on_selection_change(self, event):
        selected = self.tree.selection()
        if not selected:
            if self.drawer.is_open:
                self.drawer.close_panel()
            self.selection_callback("default", "default")
            return

        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)
        target_exam = next((e for e in self.data["exams"] if str(e["id"]) == str(item_id)), None)

        # Zidentyfikuj aktualnie wybrany obiekt danych
        current_data = target_topic or target_exam

        # Sprawdź, czy ma notatkę
        has_note_content = False
        if current_data and current_data.get("note", "").strip():
            has_note_content = True

        # Przygotuj dane do ewentualnego otwarcia
        item_for_drawer = None
        drawer_title = ""
        if current_data:
            if target_topic:
                exam = next((e for e in self.data["exams"] if e["id"] == target_topic["exam_id"]), None)
                subject_name = exam["subject"] if exam else "???"
                drawer_title = f"{subject_name}: {target_topic['name']}"
            elif target_exam:
                prefix = self.txt.get("lbl_exam_prefix", "Egzamin")
                drawer_title = f"{prefix}: {target_exam['subject']}"
            item_for_drawer = current_data

        # --- LOGIKA DECYZYJNA ---
        if has_note_content and item_for_drawer:
            # Sytuacja A: Wpis ma notatkę -> Otwórz / Zaktualizuj
            self.drawer.load_note(item_for_drawer, drawer_title)
        else:
            # Sytuacja B: Wpis NIE ma notatki.
            # Normalnie zamykamy, ALE jeśli użytkownik właśnie wymusił otwarcie (kliknął "Notes"),
            # szufladka jest otwarta na tym samym elemencie. Wtedy NIE zamykamy.
            should_close = True

            if self.drawer.is_open and self.drawer.current_item_data and current_data:
                # Jeśli ID w szufladzie zgadza się z ID zaznaczenia -> Zostaw otwarte (edycja nowej notatki)
                if str(self.drawer.current_item_data["id"]) == str(current_data["id"]):
                    should_close = False

            if should_close and self.drawer.is_open:
                self.drawer.close_panel()
            # Jeśli jest zamknięta, zostawiamy zamkniętą (ważne, by nie odpalać animacji zamykania bez potrzeby)

        # Statusy przycisków
        tags = self.tree.item(item_id, "tags")
        status_mode = "disabled"
        edit_mode = "disabled"

        if target_topic:
            edit_mode = "editable"
            if "todo" in tags:
                status_mode = "todo"
            elif "done" in tags:
                status_mode = "done"
            else:
                status_mode = "default"
        elif target_exam:
            edit_mode = "editable"
            status_mode = "disabled"
        elif str(item_id).startswith("date_"):
            edit_mode = "disabled"
            date_str = str(item_id).replace("date_", "")
            blocked_list = self.data.get("blocked_dates", [])
            status_mode = "date_blocked" if date_str in blocked_list else "date_free"

        self.selection_callback(status_mode, edit_mode)

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            self.deselect_all()
            return "break"
        if not (str(item_id).startswith("topic_") or str(item_id).startswith("exam_") or str(item_id).startswith(
                "date_")):
            self.deselect_all()
            return "break"
        return

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)
        target_exam = next((e for e in self.data["exams"] if str(e["id"]) == str(item_id)), None)
        item_to_edit = target_topic or target_exam
        if item_to_edit:
            name = item_to_edit.get("name") or item_to_edit.get("subject")
            self.drawer.load_note(item_to_edit, name)

    def deselect_all(self):
        selection = self.tree.selection()
        if selection:
            self.tree.selection_remove(selection)
            if self.drawer.is_open:
                self.drawer.close_panel()
        if self.selection_callback: self.selection_callback("default", "default")

    def toggle_status(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)
        if target_topic:
            target_topic["status"] = "done" if target_topic["status"] == "todo" else "todo"
            if target_topic["status"] == "done":
                if "global_stats" not in self.data: self.data["global_stats"] = {}
                self.data["global_stats"]["topics_done"] = self.data["global_stats"].get("topics_done", 0) + 1
                self.data["global_stats"]["activity_started"] = True
            save(self.data)
            self.refresh_table(preserve_selection=True)
            if self.dashboard_callback: self.dashboard_callback()
        elif str(item_id).startswith("date_"):
            date_str = str(item_id).replace("date_", "")
            if "blocked_dates" not in self.data: self.data["blocked_dates"] = []
            if date_str in self.data["blocked_dates"]:
                self.data["blocked_dates"].remove(date_str)
            else:
                self.data["blocked_dates"].append(date_str)
                if "global_stats" not in self.data: self.data["global_stats"] = {}
                self.data["global_stats"]["days_off"] = self.data["global_stats"].get("days_off", 0) + 1
            self.run_and_refresh()

    def run_and_refresh(self, only_unscheduled=False):
        try:
            plan(self.data, only_unscheduled=only_unscheduled)
            save(self.data)
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_plan_done"])
        except Exception as e:
            messagebox.showerror(self.txt["msg_error"], f"Error: {e}")

    def clear_database(self):
        if messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_clear_db"]):
            current_lang = self.data["settings"].get("lang", "en")
            current_theme = self.data["settings"].get("theme", "light")
            self.data["exams"] = []
            self.data["topics"] = []
            self.data["blocked_dates"] = []
            self.data["settings"] = {"max_per_day": 2, "max_same_subject_per_day": 1, "lang": current_lang,
                                     "theme": current_theme}
            save(self.data)
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_db_cleared"])

    def open_add_window(self):
        def on_add():
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

        AddExamWindow(self.win, self.txt, self.data, self.btn_style, callback=on_add)

    def open_edit(self):
        def on_edit():
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

        select_edit_item(self.win, self.data, self.txt, self.tree, self.btn_style, callback=on_edit)

    def open_archive(self):
        def edit_exam_wrapper(exam_data, callback):
            EditExamWindow(self.win, self.txt, self.data, self.btn_style, exam_data, callback)

        def edit_topic_wrapper(topic_data, callback):
            EditTopicWindow(self.win, self.txt, self.data, self.btn_style, topic_data, callback)

        ArchiveWindow(self.win, self.txt, self.data, self.btn_style, edit_exam_func=edit_exam_wrapper,
                      edit_topic_func=edit_topic_wrapper, dashboard_callback=self.dashboard_callback)

    def toggle_lock(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)
        if target_topic:
            target_topic["locked"] = not target_topic.get("locked", False)
            save(self.data)
            self.refresh_table(preserve_selection=True)

    def toggle_exam_barrier(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        target_exam = next((e for e in self.data["exams"] if str(e["id"]) == str(item_id)), None)
        if target_exam:
            target_exam["ignore_barrier"] = not target_exam.get("ignore_barrier", False)
            save(self.data)
            self.refresh_table(preserve_selection=True)
            messagebox.showinfo(self.txt["msg_info"], self.txt.get("msg_barrier_changed", "Zmieniono ustawienia."))

    def move_to_tomorrow(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)
        if target_topic:
            if target_topic.get("locked", False):
                messagebox.showwarning(self.txt["msg_info"], self.txt["msg_task_locked"])
                return
            target_topic["scheduled_date"] = str(date.today() + timedelta(days=1))
            save(self.data)
            self.refresh_table(preserve_selection=True)
            if self.dashboard_callback: self.dashboard_callback()

    def open_edit_exam_context(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]
        target_exam = next((e for e in self.data["exams"] if str(e["id"]) == str(item_id)), None)
        if target_exam:
            def on_save():
                self.refresh_table()
                if self.dashboard_callback: self.dashboard_callback()

            EditExamWindow(self.win, self.txt, self.data, self.btn_style, target_exam, on_save)

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            # Ręczne wywołanie dla pewności (Windows/Linux tego potrzebują, by zaktualizować stan)
            # Dzięki logice w on_selection_change, podwójne wywołanie jest bezpieczne.
            self.on_selection_change(None)

            if str(item_id).startswith("topic_"):
                try:
                    self.context_menu_topic.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu_topic.grab_release()
            elif str(item_id).startswith("exam_"):
                try:
                    self.context_menu_exam.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu_exam.grab_release()

    def on_drag_start(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            self.dragged_item = None
            return
        is_topic = False
        target_topic_data = None
        for topic in self.data["topics"]:
            if str(topic["id"]) == str(item_id):
                is_topic = True
                target_topic_data = topic
                break
        if is_topic:
            self.dragged_item = item_id
            item_values = self.tree.item(item_id, "values")
            display_text = f"{item_values[2]}"
            self.create_drag_tooltip(display_text, event)
        else:
            self.dragged_item = None

    def on_drag_motion(self, event):
        if self.dragged_item and self.drag_tooltip:
            x = event.x_root + 15
            y = event.y_root + 10
            self.drag_tooltip.geometry(f"+{x}+{y}")

    def on_drag_drop(self, event):
        if self.drag_tooltip:
            self.drag_tooltip.destroy()
            self.drag_tooltip = None
        if not self.dragged_item: return
        target_id = self.tree.identify_row(event.y)
        if not target_id or target_id == self.dragged_item:
            self.dragged_item = None
            return
        target_date_str = None
        current_check = target_id
        if str(current_check).startswith("date_"):
            target_date_str = str(current_check).replace("date_", "")
        else:
            while current_check:
                if str(current_check).startswith("date_"):
                    target_date_str = str(current_check).replace("date_", "")
                    break
                current_check = self.tree.prev(current_check)
        if not target_date_str:
            self.dragged_item = None
            return
        topic_found = False
        for topic in self.data["topics"]:
            if str(topic["id"]) == str(self.dragged_item):
                if topic.get("locked", False):
                    messagebox.showwarning(self.txt["msg_info"], self.txt["msg_task_locked"])
                    self.dragged_item = None
                    return
                topic["scheduled_date"] = target_date_str
                topic["locked"] = True
                topic_found = True
                break
        if topic_found:
            save(self.data)
            self.refresh_table(preserve_selection=True)
            if self.dashboard_callback: self.dashboard_callback()
        self.dragged_item = None

    def create_drag_tooltip(self, text, event):
        if self.drag_tooltip: self.drag_tooltip.destroy()
        self.drag_tooltip = tk.Toplevel(self.parent)
        self.drag_tooltip.overrideredirect(True)
        self.drag_tooltip.attributes("-topmost", True)
        x = event.x_root + 15
        y = event.y_root + 10
        self.drag_tooltip.geometry(f"+{x}+{y}")
        label = tk.Label(self.drag_tooltip, text=text, bg="#e0e0e0", fg="#000000",
                         relief="solid", borderwidth=1, padx=5, pady=2, font=("Arial", 10))
        label.pack()