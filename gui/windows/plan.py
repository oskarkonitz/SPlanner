import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date, timedelta
from core.storage import save
from core.planner import plan, date_format
from gui.windows.add_exam import AddExamWindow
from gui.windows.archive import ArchiveWindow
from gui.windows.edit import select_edit_item, EditExamWindow, EditTopicWindow
from gui.windows.note import NoteWindow


class PlanWindow():
    def __init__(self, parent, txt, data, btn_style, dashboard_callback, selection_callback):
        self.parent = parent
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback
        self.selection_callback = selection_callback

        self.win = parent

        # --- Zmienne Drag & Drop ---
        self.dragged_item = None
        self.drag_tooltip = None

        # ramka
        frame = ctk.CTkFrame(self.win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # konfiguracja tabeli
        columns = ("data", "przedmiot", "temat")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("data", text="")
        self.tree.column("data", width=55, anchor="e", stretch=False)
        self.tree.heading("przedmiot", text=self.txt["col_subject"])
        self.tree.column("przedmiot", width=150, anchor="w")
        self.tree.heading("temat", text=self.txt["col_topic_long"])
        self.tree.column("temat", width=300, anchor="w")

        # tagi dla kolorów
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

        # scrollbar
        scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=self.tree.yview, fg_color="transparent",
                                     bg_color="transparent")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.tree.pack(side="left", fill="both", expand=True)

        # --- BINDINGI ---
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        # Drag & Drop
        self.tree.bind("<ButtonPress-1>", self.on_drag_start, add="+")
        self.tree.bind("<B1-Motion>", self.on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.on_drag_drop)

        # --- Menu Kontekstowe TEMATÓW ---
        self.context_menu_topic = tk.Menu(self.tree, tearoff=0)
        self.context_menu_topic.add_command(label=self.txt.get("btn_toggle_status", "Change Status"),
                                            command=self.toggle_status)
        self.context_menu_topic.add_command(label=self.txt.get("btn_edit", "Edit"), command=self.open_edit)
        self.context_menu_topic.add_separator()
        self.context_menu_topic.add_command(label=self.txt.get("menu_notes", "Notatki"), command=self.open_notes)
        self.context_menu_topic.add_separator()
        self.context_menu_topic.add_command(label=self.txt.get("menu_lock", "Zablokuj/Odblokuj"),
                                            command=self.toggle_lock)
        self.context_menu_topic.add_separator()
        self.context_menu_topic.add_command(label=self.txt.get("menu_move_tomorrow", "Move to Tomorrow"),
                                            command=self.move_to_tomorrow)

        # --- NOWOŚĆ: Menu Kontekstowe EGZAMINÓW ---
        self.context_menu_exam = tk.Menu(self.tree, tearoff=0)
        self.context_menu_exam.add_command(label=self.txt.get("btn_edit", "Edytuj"),
                                           command=self.open_edit_exam_context)
        self.context_menu_exam.add_separator()
        self.context_menu_exam.add_command(label=self.txt.get("menu_notes", "Notatki"), command=self.open_notes_exam)
        self.context_menu_exam.add_separator()
        self.context_menu_exam.add_command(label=self.txt.get("menu_ignore_barrier", "Ignoruj w planowaniu (Bariera)"),
                                           command=self.toggle_exam_barrier)
        # -------------------------------------------

        # Binding Prawego przycisku
        if self.win.tk.call('tk', 'windowingsystem') == 'aqua':
            self.tree.bind("<Button-2>", self.show_context_menu)
            self.tree.bind("<Control-1>", self.show_context_menu)
        else:
            self.tree.bind("<Button-3>", self.show_context_menu)

        # pierwsze odswiezenia tabeli
        self.refresh_table()

    # --- NOWA FUNKCJA: Blokowanie tematu ---
    def toggle_lock(self):
        selected = self.tree.selection()
        if not selected: return

        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)

        if target_topic:
            current_state = target_topic.get("locked", False)
            target_topic["locked"] = not current_state
            save(self.data)
            self.refresh_table()

    # --- NOWA FUNKCJA: Przełączanie bariery egzaminu ---
    def toggle_exam_barrier(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        # Znajdź egzamin
        target_exam = next((e for e in self.data["exams"] if str(e["id"]) == str(item_id)), None)

        if target_exam:
            current_state = target_exam.get("ignore_barrier", False)
            target_exam["ignore_barrier"] = not current_state

            save(self.data)
            self.refresh_table()
            # Opcjonalnie: od razu przeładuj planowanie, bo to wpływa na algorytm
            # self.run_and_refresh()
            messagebox.showinfo(self.txt["msg_info"], self.txt.get("msg_barrier_changed",
                                                                   "Zmieniono ustawienia planowania. Wygeneruj plan ponownie."))

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

    # --- Notatki dla Tematu ---
    def open_notes(self):
        selected = self.tree.selection()
        if not selected: return

        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)

        if target_topic:
            win = NoteWindow(self.win, self.txt, self.data, self.btn_style, target_topic)
            self.win.wait_window(win.win)
            self.refresh_table()

    # --- NOWA FUNKCJA: Notatki dla Egzaminu ---
    def open_notes_exam(self):
        selected = self.tree.selection()
        if not selected: return

        item_id = selected[0]
        target_exam = next((e for e in self.data["exams"] if str(e["id"]) == str(item_id)), None)

        if target_exam:
            win = NoteWindow(self.win, self.txt, self.data, self.btn_style, target_exam)
            self.win.wait_window(win.win)
            self.refresh_table()

    # --- Menu Kontekstowe (Rozdzielacz) ---
    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
            self.on_selection_change(None)

            # Sprawdzamy czy to temat
            is_topic = False
            for t in self.data["topics"]:
                if str(t["id"]) == str(item_id):
                    is_topic = True
                    break

            # Sprawdzamy czy to egzamin
            is_exam = False
            for e in self.data["exams"]:
                if str(e["id"]) == str(item_id):
                    is_exam = True
                    break

            if is_topic:
                try:
                    self.context_menu_topic.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu_topic.grab_release()

            elif is_exam:
                try:
                    self.context_menu_exam.tk_popup(event.x_root, event.y_root)
                finally:
                    self.context_menu_exam.grab_release()

    def move_to_tomorrow(self):
        selected = self.tree.selection()
        if not selected: return

        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)

        if target_topic:
            if target_topic.get("locked", False):
                messagebox.showwarning(self.txt["msg_info"], self.txt["msg_task_locked"])
                return

            today = date.today()
            tomorrow = today + timedelta(days=1)

            target_topic["scheduled_date"] = str(tomorrow)
            save(self.data)
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

    # --- DRAG & DROP ---
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
            display_text = f"{item_values[1]}: {item_values[2]}"
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

        if not self.dragged_item:
            return

        target_id = self.tree.identify_row(event.y)
        if not target_id:
            self.dragged_item = None
            return

        if target_id == self.dragged_item:
            self.dragged_item = None
            return

        target_date_str = None
        current_check = target_id

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
                topic_found = True
                break

        if topic_found:
            save(self.data)
            self.refresh_table()
            if self.dashboard_callback:
                self.dashboard_callback()

        self.dragged_item = None

    def create_drag_tooltip(self, text, event):
        if self.drag_tooltip:
            self.drag_tooltip.destroy()

        self.drag_tooltip = tk.Toplevel(self.parent)
        self.drag_tooltip.overrideredirect(True)
        self.drag_tooltip.attributes("-topmost", True)

        x = event.x_root + 15
        y = event.y_root + 10
        self.drag_tooltip.geometry(f"+{x}+{y}")

        label = tk.Label(self.drag_tooltip, text=text, bg="#e0e0e0", fg="#000000",
                         relief="solid", borderwidth=1, padx=5, pady=2, font=("Arial", 10))
        label.pack()

    # --- Reszta ---
    def on_selection_change(self, event):
        selected = self.tree.selection()
        if not selected:
            self.selection_callback("default", "default")
            return

        item_id = selected[0]
        tags = self.tree.item(item_id, "tags")

        status_mode = "disabled"
        edit_mode = "disabled"

        if str(item_id).startswith("topic_") or any(str(t["id"]) == str(item_id) for t in self.data["topics"]):
            edit_mode = "editable"
            if "todo" in tags:
                status_mode = "todo"
            elif "done" in tags:
                status_mode = "done"
            else:
                status_mode = "default"

        elif str(item_id).startswith("exam_"):
            edit_mode = "editable"
            status_mode = "disabled"

        elif str(item_id).startswith("date_"):
            edit_mode = "disabled"
            date_str = str(item_id).replace("date_", "")
            blocked_list = self.data.get("blocked_dates", [])

            if date_str in blocked_list:
                status_mode = "date_blocked"
            else:
                status_mode = "date_free"

        self.selection_callback(status_mode, edit_mode)

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            self.deselect_all()
            return "break"

        is_interactive = str(item_id).startswith("exam_") or str(item_id).startswith("date_")
        if not is_interactive:
            for t in self.data["topics"]:
                if str(t["id"]) == str(item_id):
                    is_interactive = True
                    break

        # Dodatkowe sprawdzenie, żeby nie odznaczało przy klikaniu w Egzaminy
        if not is_interactive:
            # check exams
            for e in self.data["exams"]:
                if str(e["id"]) == str(item_id):
                    is_interactive = True
                    break

        if not is_interactive:
            self.deselect_all()
            return "break"
        return

    def deselect_all(self):
        selection = self.tree.selection()
        if selection:
            self.tree.selection_remove(selection)
        if self.selection_callback:
            self.selection_callback("default", "default")

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree.insert("", "end", values=("", "", ""))

        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= date.today()}
        overdue_topics = [
            t for t in self.data["topics"]
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < date.today()
               and t["status"] == "todo" and t["exam_id"] in active_exams_ids
        ]

        # --- ZALEGŁE ---
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
                if has_note: marks += "✎"
                if is_locked: marks += "☒"

                self.tree.insert("", "end", iid=topic["id"],
                                 values=(marks, f"{topic['scheduled_date']}\t{subj_name}", topic["name"]),
                                 tags=("overdue",))
            self.tree.insert("", "end", values=("", "", ""))

        # --- PRZYGOTOWANIE DAT ---
        all_dates = set()
        for exam in self.data["exams"]:
            if date_format(exam["date"]) >= date.today():
                all_dates.add(str(exam["date"]))
        for topic in self.data["topics"]:
            if topic["scheduled_date"] and date_format(topic["scheduled_date"]) >= date.today():
                all_dates.add(str(topic["scheduled_date"]))

        blocked_list = self.data.get("blocked_dates", [])
        if all_dates:
            min_d = min(all_dates)
            max_d = max(all_dates)
            for bd in blocked_list:
                if bd >= str(date.today()) and (not all_dates or bd <= max_d):
                    all_dates.add(bd)

        sorted_dates = sorted(list(all_dates))

        # --- GŁÓWNA PĘTLA PO DNIACH ---
        for day_str in sorted_dates:
            todays_exams = [e for e in self.data["exams"] if e["date"] == day_str]
            todays_topics = [t for t in self.data["topics"] if str(t.get("scheduled_date")) == day_str]

            is_blocked = day_str in blocked_list
            has_exams = len(todays_exams) > 0

            days_left = (date_format(day_str) - date.today()).days
            display_text = ""
            tag = "normal"
            icon = "●"

            # --- LOGIKA ETYKIETY I KOLORU ---
            # 1. Jeśli dzień jest zablokowany I NIE MA egzaminu -> Wygląd "Day Off" (szary)
            if is_blocked and not has_exams:
                display_text = self.txt.get("tag_day_off", "(Day Off)")
                tag = "blocked"
                icon = "○"

            # 2. W przeciwnym razie (Normalny dzień LUB Zablokowany ale Z EGZAMINEM) -> Wygląd standardowy/egzaminacyjny
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

                # Jeśli jest zablokowany (ale ma egzamin), dodajemy dopisek i zmieniamy ikonę na pustą
                if is_blocked:
                    day_off_txt = self.txt.get("tag_day_off", "(Day Off)")
                    display_text += f" {day_off_txt}"
                    icon = "○"

            full_label = f"{display_text} ({day_str})"
            self.tree.insert("", "end", iid=f"date_{day_str}", values=(icon, full_label, ""), tags=(tag,))

            # --- WYŚWIETLANIE ZAWARTOŚCI DNIA ---
            # Pokazujemy zawartość jeśli dzień NIE jest zablokowany LUB jeśli MA egzaminy
            if not is_blocked or has_exams:
                self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))

                # Egzaminy pokazujemy ZAWSZE (jeśli istnieją w tym dniu)
                for exam in todays_exams:
                    marks = ""
                    if exam.get("note", "").strip(): marks += "✎"
                    if exam.get("ignore_barrier", False): marks += "ø"

                    self.tree.insert("", "end", iid=exam["id"],
                                     values=(f"{marks} │", exam["subject"], exam["title"]),
                                     tags=("exam",))

                # Tematy pokazujemy TYLKO jeśli dzień NIE jest zablokowany
                # (Bo jeśli jest Day Off, to się nie uczymy tematów, nawet jak jest egzamin)
                if not is_blocked:
                    if len(todays_exams) > 0 and len(todays_topics) > 0:
                        self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))

                    for topic in todays_topics:
                        subj_name = self.txt["val_other"]
                        for exam in self.data["exams"]:
                            if exam["id"] == topic["exam_id"]:
                                subj_name = exam["subject"]
                                break

                        has_note = topic.get("note", "").strip()
                        is_locked = topic.get("locked", False)
                        marks = ""
                        if has_note: marks += "✎"
                        if is_locked: marks += "☒"

                        col_0 = f"{marks} │"

                        self.tree.insert("", "end", iid=topic["id"], values=(col_0, subj_name, topic["name"]),
                                         tags=(topic["status"],))

                self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))

            # Odstęp po dniu
            self.tree.insert("", "end", values=("", "", ""))

    def run_and_refresh(self, only_unscheduled=False):
        try:
            plan(self.data, only_unscheduled=only_unscheduled)
            save(self.data)
            self.refresh_table()

            if self.dashboard_callback: self.dashboard_callback()

            msg_key = "msg_plan_done"
            messagebox.showinfo(self.txt["msg_success"], self.txt[msg_key])
        except Exception as e:
            messagebox.showerror(self.txt["msg_error"], f"Error: {e}")

    def toggle_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_status"])
            return

        item_id = selected[0]
        target_topic = next((t for t in self.data["topics"] if str(t["id"]) == str(item_id)), None)

        if target_topic:
            target_topic["status"] = "done" if target_topic["status"] == "todo" else "todo"
            save(self.data)

            new_tag = target_topic["status"]
            self.tree.item(item_id, tags=(new_tag,))

            if self.dashboard_callback: self.dashboard_callback()
            self.on_selection_change(None)

        elif str(item_id).startswith("date_"):
            date_str = str(item_id).replace("date_", "")
            if "blocked_dates" not in self.data:
                self.data["blocked_dates"] = []

            if date_str in self.data["blocked_dates"]:
                self.data["blocked_dates"].remove(date_str)
            else:
                self.data["blocked_dates"].append(date_str)

            self.run_and_refresh()

        else:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_cant_status"])

    def clear_database(self):
        if messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_clear_db"]):
            current_lang = self.data["settings"].get("lang", "en")
            self.data["exams"] = []
            self.data["topics"] = []
            self.data["blocked_dates"] = []
            self.data["settings"] = {
                "max_per_day": 2,
                "max_same_subject_per_day": 1,
                "lang": current_lang
            }
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
                      edit_topic_func=edit_topic_wrapper)