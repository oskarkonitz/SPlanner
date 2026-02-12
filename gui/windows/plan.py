import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date, timedelta
from core.planner import plan, date_format
from gui.dialogs.add_exam import AddExamWindow
from gui.windows.archive import ArchiveWindow
from gui.dialogs.edit import select_edit_item, EditExamWindow, EditTopicWindow
from gui.components.drawers import NoteDrawer

# --- GŁÓWNA KLASA OKNA PLANU ---
class PlanWindow:
    def __init__(self, parent, txt, btn_style, dashboard_callback, selection_callback, drawer_parent=None,
                 storage=None):
        self.parent = parent
        self.txt = txt
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback
        self.selection_callback = selection_callback
        self.win = parent
        self.storage = storage  # Źródło prawdy

        draw_target = drawer_parent if drawer_parent else self.win

        self.dragged_item = None
        self.drag_tooltip = None

        self.table_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=0, pady=8)

        columns = ("data", "przedmiot", "temat")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="tree", selectmode="browse")
        self.tree.column("#0", width=0, stretch=False)

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

        self.lbl_empty = ctk.CTkLabel(self.table_frame,
                                      text=self.txt.get("msg_empty_plan", "No exams."),
                                      font=("Arial", 16, "bold"),
                                      text_color="gray")

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

        self.drawer = NoteDrawer(draw_target, self.txt, self.btn_style, self.save_data_from_drawer)

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
            stats = self.storage.get_global_stats()
            curr = stats.get("notes_added", 0)
            self.storage.update_global_stat("notes_added", curr + 1)

        # Dane zostały już zaktualizowane w pamięci (referencja self.current_item_data w drawer)
        # Teraz musimy je zrzucić do SQL
        if self.storage and self.drawer.current_item_data:
            item = self.drawer.current_item_data
            # Rozróżniamy temat od egzaminu
            if "exam_id" in item:
                self.storage.update_topic(item)
            else:
                self.storage.update_exam(item)

        self.refresh_table(preserve_selection=True)
        if self.dashboard_callback: self.dashboard_callback()

    # --- METODY DLA NOWYCH PRZYCISKÓW ---
    def delete_selected_item(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        # Sprawdzamy czy to egzamin (szybki SQL)
        target_exam = self.storage.get_exam(item_id)

        if target_exam:
            if messagebox.askyesno(self.txt["msg_warning"],
                                   self.txt["msg_confirm_del_exam"].format(subject=target_exam["subject"])):
                self.storage.delete_exam(target_exam["id"])
                self.refresh_table()
                if self.dashboard_callback: self.dashboard_callback()
            return

        # Sprawdzamy czy to temat (szybki SQL)
        target_topic = self.storage.get_topic(item_id)

        if target_topic:
            if messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_topic"]):
                self.storage.delete_topic(target_topic["id"])
                self.refresh_table()
                if self.dashboard_callback: self.dashboard_callback()

    def restore_status(self):
        # Cofanie statusu Done -> Todo
        self.toggle_status()

    def move_selected_to_today(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        # Szybkie pobranie tematu
        target_topic = self.storage.get_topic(item_id)

        if target_topic:
            target_topic["scheduled_date"] = str(date.today())
            target_topic["locked"] = True  # Blokujemy, żeby algorytm nie zabrał

            self.storage.update_topic(target_topic)
            self.refresh_table(preserve_selection=True)
            if self.dashboard_callback: self.dashboard_callback()

    # --- LOGIKA OTWIERANIA NOTATEK Z MENU ---
    def open_notes(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_topic = self.storage.get_topic(item_id)

        if target_topic:
            # Pobieramy egzamin dla nazwy (szybki SQL)
            exam_row = self.storage.get_exam(target_topic["exam_id"])
            subject_name = exam_row["subject"] if exam_row else "???"

            drawer_title = f"{subject_name}: {target_topic['name']}"
            self.drawer.load_note(target_topic, drawer_title)

    def open_notes_exam(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_exam = self.storage.get_exam(item_id)

        if target_exam:
            prefix = self.txt.get("lbl_exam_prefix", "Egzamin")
            drawer_title = f"{prefix}: {target_exam['subject']}"
            self.drawer.load_note(target_exam, drawer_title)

    def refresh_table(self, only_unscheduled=False, preserve_selection=False):
        # --- PURE SQL: POBIERANIE DANYCH ON-DEMAND ---
        # Konwersja Row -> dict + bool dla wygody w GUI
        exams = []
        for r in self.storage.get_exams():
            d = dict(r)
            d["ignore_barrier"] = bool(d["ignore_barrier"])
            exams.append(d)

        topics = []
        for r in self.storage.get_topics():
            d = dict(r)
            d["locked"] = bool(d["locked"])
            topics.append(d)

        blocked_dates = self.storage.get_blocked_dates()

        selected_id = None
        if preserve_selection:
            sel = self.tree.selection()
            if sel: selected_id = sel[0]

        for item in self.tree.get_children():
            self.tree.delete(item)

        # 1. ZALEGŁE
        self.tree.insert("", "end", values=("", "", ""))
        active_exams_ids = {e["id"] for e in exams if date_format(e["date"]) >= date.today()}
        overdue_topics = [
            t for t in topics
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < date.today()
               and t["status"] == "todo" and t["exam_id"] in active_exams_ids
        ]

        if overdue_topics:
            self.tree.insert("", "end", values=("", self.txt["tag_overdue"], ""), tags=("overdue",))
            for topic in overdue_topics:
                subj_name = self.txt["val_other"]
                for exam in exams:
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

        # 2. DATY (Główna pętla)
        all_dates = set()
        for exam in exams:
            if date_format(exam["date"]) >= date.today():
                all_dates.add(str(exam["date"]))
        for topic in topics:
            if topic.get("scheduled_date") and date_format(topic["scheduled_date"]) >= date.today():
                all_dates.add(str(topic["scheduled_date"]))

        if all_dates:
            for bd in blocked_dates:
                if bd >= str(date.today()) and bd <= max(all_dates):
                    all_dates.add(bd)

        sorted_dates = sorted(list(all_dates))

        # Rysowanie wierszy...
        for day_str in sorted_dates:
            todays_exams = [e for e in exams if e["date"] == day_str]
            todays_topics = [t for t in topics if str(t.get("scheduled_date")) == day_str]
            is_blocked = day_str in blocked_dates
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

            weekday_idx = date_format(day_str).weekday()
            day_name = self.txt["days_short"][weekday_idx]

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
                        subj_name = self.txt["val_other"]
                        parent_exam = None
                        for exam in exams:
                            if exam["id"] == topic["exam_id"]:
                                subj_name = exam["subject"]
                                parent_exam = exam
                                break

                        has_note = topic.get("note", "").strip()
                        marks = " ✎" if has_note else ""
                        if topic.get("locked", False): marks += " ☒"

                        final_tags = []
                        if topic["status"] == "done":
                            final_tags.append("done")
                        else:
                            if parent_exam and parent_exam.get("color"):
                                col = parent_exam["color"]
                                tag_col_name = f"theme_{parent_exam['id']}"
                                self.tree.tag_configure(tag_col_name, foreground=col, font=("Arial", 13, "bold"))
                                final_tags.append(tag_col_name)
                            else:
                                final_tags.append("todo")

                        self.tree.insert("", "end", iid=topic["id"],
                                         values=(f"{marks} │", subj_name, topic["name"]),
                                         tags=tuple(final_tags))
                self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))
            self.tree.insert("", "end", values=("", "", ""))

        if selected_id and self.tree.exists(selected_id):
            self.tree.selection_set(selected_id)
            self.tree.see(selected_id)

        # --- LOGIKA PUSTEGO STANU ---
        has_future_items = len(sorted_dates) > 0
        has_overdue_items = len(overdue_topics) > 0

        if not has_future_items and not has_overdue_items:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_empty.lift()
        else:
            self.lbl_empty.place_forget()

    # --- ZMIANA ZAZNACZENIA ---
    def on_selection_change(self, event):
        selected = self.tree.selection()

        if not selected:
            if self.drawer.is_open: self.drawer.close_panel()
            self.selection_callback("idle", None, None)
            return

        item_id = selected[0]

        # Pobieranie danych on-demand (szybki SQL)
        target_topic = self.storage.get_topic(item_id)
        target_exam = self.storage.get_exam(item_id)
        blocked_dates = self.storage.get_blocked_dates()

        is_date = str(item_id).startswith("date_")

        # --- LOGIKA PRZYCISKÓW ---
        state_1 = "disabled"
        state_2 = "disabled"
        state_3 = "disabled"

        if target_topic:
            # Temat
            is_done = target_topic["status"] == "done"
            is_overdue = False
            if target_topic.get("scheduled_date") and date_format(
                    target_topic["scheduled_date"]) < date.today() and not is_done:
                is_overdue = True

            if is_overdue:
                state_1 = "complete"  # Góra: Done
                state_2 = "move_today"  # Środek: Move to Today
                state_3 = "edit_topic"  # Dół: Edit
            elif is_done:
                state_1 = "restore"  # Góra: Restore
                state_2 = "edit_topic"  # Środek: Edit
                state_3 = "delete"  # Dół: Delete
            else:
                state_1 = "complete"  # Góra: Done
                state_2 = "edit_topic"  # Środek: Edit
                state_3 = "delete"  # Dół: Delete

        elif target_exam:
            # Egzamin
            state_1 = "hidden"
            state_2 = "edit_exam"
            state_3 = "delete"

        elif is_date:
            # Data
            date_str = str(item_id).replace("date_", "")
            is_blocked = date_str in blocked_dates

            if is_blocked:
                state_1 = "unblock"
                state_2 = "unblock_gen"
            else:
                state_1 = "block"
                state_2 = "block_gen"

            state_3 = "hidden"

        self.selection_callback(state_1, state_2, state_3)

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

        # Próbujemy pobrać temat, jak nie ma to egzamin
        item_to_edit = self.storage.get_topic(item_id)
        if not item_to_edit:
            item_to_edit = self.storage.get_exam(item_id)

        if item_to_edit:
            name = item_to_edit.get("name") or item_to_edit.get("subject")
            self.drawer.load_note(item_to_edit, name)

    def deselect_all(self):
        selection = self.tree.selection()
        if selection:
            self.tree.selection_remove(selection)
            if self.drawer.is_open:
                self.drawer.close_panel()

        if self.selection_callback:
            self.selection_callback("idle", "idle", "idle")

    def toggle_status(self, generate=True):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        # Pobieramy on-demand (szybki SQL)
        target_topic = self.storage.get_topic(item_id)

        # --- ZMIANA STATUSU TEMATU ---
        if target_topic:
            target_topic["status"] = "done" if target_topic["status"] == "todo" else "todo"

            self.storage.update_topic(target_topic)

            if target_topic["status"] == "done":
                stats = self.storage.get_global_stats()
                done_count = stats.get("topics_done", 0) + 1
                self.storage.update_global_stat("topics_done", done_count)
                self.storage.update_global_stat("activity_started", True)

            self.refresh_table(preserve_selection=True)
            if self.dashboard_callback: self.dashboard_callback()

        # --- BLOKOWANIE / ODBLOKOWANIE DATY ---
        elif str(item_id).startswith("date_"):
            date_str = str(item_id).replace("date_", "")

            blocked_dates = self.storage.get_blocked_dates()

            if date_str in blocked_dates:
                self.storage.remove_blocked_date(date_str)
            else:
                stats = self.storage.get_global_stats()
                days_off = stats.get("days_off", 0) + 1
                self.storage.update_global_stat("days_off", days_off)
                self.storage.add_blocked_date(date_str)

            if generate:
                self.run_and_refresh()
            else:
                self.refresh_table(preserve_selection=True)
                if self.dashboard_callback: self.dashboard_callback()

    def run_and_refresh(self, only_unscheduled=False):
        try:
            if not self.storage:
                messagebox.showerror(self.txt["msg_error"], "Brak połączenia z bazą danych.")
                return

            # Uruchamiamy planer BEZPOŚREDNIO na bazie danych (Pure SQL)
            plan(self.storage, only_unscheduled=only_unscheduled)

            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_plan_done"])
        except Exception as e:
            messagebox.showerror(self.txt["msg_error"], f"Error: {e}")
            print(f"DEBUG ERROR: {e}")

    def open_add_window(self):
        def on_add():
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

        AddExamWindow(self.win, self.txt, self.btn_style, callback=on_add, storage=self.storage)

    def open_edit(self):
        def on_edit():
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

        select_edit_item(self.win, self.txt, self.tree, self.btn_style, callback=on_edit,
                         storage=self.storage)

    def open_archive(self):
        def edit_exam_wrapper(exam_data, callback):
            EditExamWindow(self.win, self.txt, self.btn_style, exam_data, callback, storage=self.storage)

        def edit_topic_wrapper(topic_data, callback):
            EditTopicWindow(self.win, self.txt, self.btn_style, topic_data, callback, storage=self.storage)

        ArchiveWindow(self.win, self.txt, self.btn_style, edit_exam_func=edit_exam_wrapper,
                      edit_topic_func=edit_topic_wrapper, dashboard_callback=self.dashboard_callback,
                      storage=self.storage)

    def toggle_lock(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_topic = self.storage.get_topic(item_id)

        if target_topic:
            target_topic["locked"] = not target_topic.get("locked", False)
            self.storage.update_topic(target_topic)
            self.refresh_table(preserve_selection=True)

    def toggle_exam_barrier(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_exam = self.storage.get_exam(item_id)

        if target_exam:
            target_exam["ignore_barrier"] = not target_exam.get("ignore_barrier", False)
            self.storage.update_exam(target_exam)
            self.refresh_table(preserve_selection=True)
            messagebox.showinfo(self.txt["msg_info"], self.txt.get("msg_barrier_changed", "Zmieniono ustawienia."))

    def move_to_tomorrow(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_topic = self.storage.get_topic(item_id)

        if target_topic:
            if target_topic.get("locked", False):
                messagebox.showwarning(self.txt["msg_info"], self.txt["msg_task_locked"])
                return
            target_topic["scheduled_date"] = str(date.today() + timedelta(days=1))

            self.storage.update_topic(target_topic)
            self.refresh_table(preserve_selection=True)
            if self.dashboard_callback: self.dashboard_callback()

    def open_edit_exam_context(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_exam = self.storage.get_exam(item_id)

        if target_exam:
            def on_save():
                self.refresh_table()
                if self.dashboard_callback: self.dashboard_callback()

            EditExamWindow(self.win, self.txt, self.btn_style, target_exam, on_save, storage=self.storage)

    def show_context_menu(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            self.tree.selection_set(item_id)
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

        # Szybki SQL
        topic_data = self.storage.get_topic(item_id)

        if topic_data:
            is_topic = True

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

        # Szybkie pobranie tematu
        topic = self.storage.get_topic(self.dragged_item)

        topic_found = False
        if topic:
            if topic.get("locked", False):
                messagebox.showwarning(self.txt["msg_info"], self.txt["msg_task_locked"])
                self.dragged_item = None
                return
            topic["scheduled_date"] = target_date_str
            topic["locked"] = True
            topic_found = True

            self.storage.update_topic(topic)

        if topic_found:
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