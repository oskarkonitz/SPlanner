import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from datetime import date, timedelta
from core.storage import save
from core.planner import plan, date_format
from gui.windows.add_exam import AddExamWindow
from gui.windows.archive import ArchiveWindow
from gui.windows.edit import select_edit_item, EditExamWindow, EditTopicWindow


class PlanWindow():
    def __init__(self, parent, txt, data, btn_style, dashboard_callback, selection_callback):
        self.parent = parent
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback
        self.selection_callback = selection_callback

        self.win = parent

        # ramka
        frame = ctk.CTkFrame(self.win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # konfiguracja tabeli
        columns = ("data", "przedmiot", "temat")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("data", text="")
        self.tree.column("data", width=45, anchor="e", stretch=False)
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

        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        # pierwsze odswiezenia tabeli
        self.refresh_table()

    def on_selection_change(self, event):
        selected = self.tree.selection()

        # 1. Nic nie zaznaczone
        if not selected:
            self.selection_callback("default", "default")
            return

        item_id = selected[0]
        tags = self.tree.item(item_id, "tags")

        # --- ZMIANA: Domyślnie ustawiamy tryb na 'disabled' (szary/brak reakcji) ---
        status_mode = "disabled"
        edit_mode = "disabled"

        # 2. Rozpoznawanie elementu
        if item_id.startswith("topic_"):
            # Temat: Edycja aktywna, Status zależny od todo/done
            edit_mode = "editable"
            if "todo" in tags:
                status_mode = "todo"
            elif "done" in tags:
                status_mode = "done"
            else:
                status_mode = "default"

        elif item_id.startswith("exam_"):
            # Egzamin: Edycja aktywna, Status zablokowany (czerwony - bo egzaminu nie odhaczamy)
            edit_mode = "editable"
            status_mode = "locked"

        elif item_id.startswith("date_"):
            # Data: Edycja WYŁĄCZONA (szara), Status aktywny (Blokuj/Odblokuj)
            edit_mode = "disabled"

            date_str = item_id.replace("date_", "")
            blocked_list = self.data.get("blocked_dates", [])

            if date_str in blocked_list:
                status_mode = "date_blocked"
            else:
                status_mode = "date_free"

        # W przypadku separatorów/pustych linii wchodzimy w domyślny stan "disabled",
        # więc przyciski nie będą się podświetlać na czerwono.

        self.selection_callback(status_mode, edit_mode)

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)

        if not item_id:
            self.deselect_all()
            return

        is_interactive = item_id.startswith("exam_") or item_id.startswith("topic_") or item_id.startswith("date_")

        if not is_interactive:
            self.deselect_all()
            return "break"

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

        if overdue_topics:
            self.tree.insert("", "end", values=("", self.txt["tag_overdue"], ""), tags=("overdue",))
            for topic in overdue_topics:
                subj_name = self.txt["val_other"]
                for exam in self.data["exams"]:
                    if exam["id"] == topic["exam_id"]:
                        subj_name = exam["subject"]
                        break
                self.tree.insert("", "end", iid=topic["id"],
                                 values=("", f"{topic["scheduled_date"]}\t{subj_name}", topic["name"]),
                                 tags=("overdue",))
            self.tree.insert("", "end", values=("", "", ""))

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

        for day_str in sorted_dates:
            todays_exams = [e for e in self.data["exams"] if e["date"] == day_str]
            todays_topics = [t for t in self.data["topics"] if str(t.get("scheduled_date")) == day_str]

            is_blocked = day_str in blocked_list
            days_left = (date_format(day_str) - date.today()).days
            display_text = ""
            tag = "normal"

            if is_blocked:
                display_text = self.txt.get("tag_day_off", "(Day Off)")
                tag = "blocked"
            elif days_left == 0:
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

            full_label = f"{display_text} ({day_str})"
            icon = "●"
            if is_blocked: icon = "○"

            self.tree.insert("", "end", iid=f"date_{day_str}", values=(icon, full_label, ""), tags=(tag,))

            if not is_blocked:
                self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))

                for exam in todays_exams:
                    self.tree.insert("", "end", iid=exam["id"], values=("│", exam["subject"], exam["title"]),
                                     tags=("exam",))

                if len(todays_exams) > 0 and len(todays_topics) > 0:
                    self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))

                for topic in todays_topics:
                    subj_name = self.txt["val_other"]
                    for exam in self.data["exams"]:
                        if exam["id"] == topic["exam_id"]:
                            subj_name = exam["subject"]
                            break
                    self.tree.insert("", "end", iid=topic["id"], values=("│", subj_name, topic["name"]),
                                     tags=(topic["status"],))

                self.tree.insert("", "end", values=("│", "", ""), tags=("todo",))
            else:
                pass

            self.tree.insert("", "end", values=("", "", ""))

    def run_and_refresh(self):
        try:
            plan(self.data)
            save(self.data)
            self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_plan_done"])
        except Exception as e:
            messagebox.showerror(self.txt["msg_error"], f"Error: {e}")

    def toggle_status(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo(self.txt["msg_info"], self.txt["msg_select_status"])
            return

        item_id = selected[0]

        if item_id.startswith("topic_"):
            target_topic = next((t for t in self.data["topics"] if t["id"] == item_id), None)
            if target_topic:
                target_topic["status"] = "done" if target_topic["status"] == "todo" else "todo"
                save(self.data)

                new_tag = target_topic["status"]
                self.tree.item(item_id, tags=(new_tag,))

                if self.dashboard_callback: self.dashboard_callback()
                self.on_selection_change(None)

        elif item_id.startswith("date_"):
            date_str = item_id.replace("date_", "")
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