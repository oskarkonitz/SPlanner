import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import customtkinter as ctk
from datetime import date, timedelta, datetime
import uuid
from tkcalendar import Calendar
from core.storage import save


class TodoWindow:
    # ZMIANA: Dodano argument dashboard_callback
    def __init__(self, parent, txt, data, btn_style, dashboard_callback):
        self.parent = parent
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback  # Zapisujemy callback

        if "daily_tasks" not in self.data:
            self.data["daily_tasks"] = []

        self.current_color = None
        self.selected_task_id = None

        # --- GÓRNY PASEK ---
        self.top_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=5, pady=(5, 5))

        # Pole Zadania
        placeholder = self.txt.get("todo_placeholder", "Enter task...")
        self.entry_task = ctk.CTkEntry(self.top_frame, placeholder_text=placeholder, height=35)
        self.entry_task.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Data
        self.date_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.date_frame.pack(side="left", padx=(0, 5))

        self.entry_date = ctk.CTkEntry(self.date_frame, width=100, height=35, justify="center")
        self.entry_date.insert(0, str(date.today()))
        self.entry_date.pack(side="left", padx=(0, 2))

        self.btn_cal = ctk.CTkButton(self.date_frame, text="📅", width=35,
                                     command=self.open_calendar_popup,
                                     **self.btn_style)
        self.btn_cal.pack(side="left")

        # Kolor
        self.btn_color = ctk.CTkButton(self.top_frame, text="", width=35, height=35,
                                       fg_color="transparent",
                                       border_width=2, border_color="gray",
                                       command=self.pick_color)
        self.btn_color.pack(side="left", padx=(0, 5))

        # Akcja
        self.btn_action = ctk.CTkButton(self.top_frame, text="+", width=35,
                                        command=self.save_task,
                                        **self.btn_style)
        self.btn_action.pack(side="left")

        # --- TABELA ---
        self.table_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=0, pady=8)

        columns = ("status", "task")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("status", text=self.txt.get("col_status", "Status"))
        self.tree.column("status", width=60, anchor="center", stretch=False)

        self.tree.heading("task", text=self.txt.get("col_task", "Task"))
        self.tree.column("task", width=500, anchor="w")

        # Style
        self.tree.tag_configure("done", foreground="#00b800", font=("Arial", 13, "bold"))
        self.tree.tag_configure("header", font=("Arial", 13, "bold"), foreground="#e6b800")
        self.tree.tag_configure("default", font=("Arial", 13, "bold"))
        self.tree.tag_configure("overdue_header", foreground="#e74c3c", font=("Arial", 13, "bold"))
        self.tree.tag_configure("overdue_item", font=("Arial", 13, "bold"))

        scrollbar = ctk.CTkScrollbar(self.table_frame, orientation="vertical", command=self.tree.yview,
                                     fg_color="transparent", bg_color="transparent")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<Double-1>", self.toggle_status)
        self.tree.bind("<Delete>", self.delete_task)
        self.tree.bind("<Button-1>", self.on_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # Menu kontekstowe
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label=self.txt.get("btn_toggle_status", "Change Status"),
                                      command=self.toggle_status)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.txt.get("menu_move_tomorrow", "Move to tomorrow"),
                                      command=self.move_to_tomorrow)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.txt.get("btn_delete", "Delete"), command=self.delete_task)

        if self.parent.tk.call('tk', 'windowingsystem') == 'aqua':
            self.tree.bind("<Button-2>", self.show_context_menu)
        else:
            self.tree.bind("<Button-3>", self.show_context_menu)

        self.refresh_table()

    def open_calendar_popup(self):
        try:
            current_date_str = self.entry_date.get()
            y, m, d = map(int, current_date_str.split("-"))
        except:
            d_obj = date.today()
            y, m, d = d_obj.year, d_obj.month, d_obj.day

        top = ctk.CTkToplevel(self.parent)
        title = self.txt.get("win_date_picker", "Select Date")
        top.title(title)
        top.geometry("300x250")
        top.attributes("-topmost", True)

        cal = Calendar(top, selectmode='day', year=y, month=m, day=d, date_pattern="yyyy-mm-dd")
        cal.pack(pady=20, padx=20, fill="both", expand=True)

        def set_date():
            self.entry_date.delete(0, "end")
            self.entry_date.insert(0, cal.get_date())
            top.destroy()

        btn_txt = self.txt.get("btn_select", "Select")
        ctk.CTkButton(top, text=btn_txt, command=set_date).pack(pady=(0, 20))

    def pick_color(self):
        title = self.txt.get("win_color_picker_task", "Task Color")
        color = askcolor(color=self.current_color, title=title)[1]
        if color:
            self.current_color = color
            self.btn_color.configure(fg_color=color)

    def save_task(self):
        content = self.entry_task.get().strip()
        date_val = self.entry_date.get().strip()

        if not content: return

        if self.selected_task_id:
            for t in self.data["daily_tasks"]:
                if t["id"] == self.selected_task_id:
                    t["content"] = content
                    t["date"] = date_val
                    t["color"] = self.current_color
                    break
            self.deselect_all()
        else:
            new_task = {
                "id": str(uuid.uuid4()),
                "content": content,
                "status": "todo",
                "created_at": str(date.today()),
                "date": date_val,
                "color": self.current_color
            }
            self.data["daily_tasks"].append(new_task)
            self.entry_task.delete(0, "end")
            self.current_color = None
            self.btn_color.configure(fg_color="transparent")

        save(self.data)
        self.refresh_table()
        # ZMIANA: Wywołanie odświeżania statystyk
        if self.dashboard_callback: self.dashboard_callback()

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        task = next((t for t in self.data["daily_tasks"] if t["id"] == item_id), None)
        if task:
            self.selected_task_id = item_id
            self.entry_task.delete(0, "end")
            self.entry_task.insert(0, task["content"])
            self.entry_date.delete(0, "end")
            self.entry_date.insert(0, task.get("date", str(date.today())))

            self.current_color = task.get("color")
            if self.current_color:
                self.btn_color.configure(fg_color=self.current_color)
            else:
                self.btn_color.configure(fg_color="transparent")

            self.btn_action.configure(text="✓")

    def deselect_all(self):
        selection = self.tree.selection()
        if selection:
            self.tree.selection_remove(selection)
        self.selected_task_id = None
        self.entry_task.delete(0, "end")
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, str(date.today()))
        self.current_color = None
        self.btn_color.configure(fg_color="transparent")
        self.btn_action.configure(text="+")
        self.parent.focus_set()

    def on_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            self.deselect_all()

    def refresh_table(self):
        sel_id = self.selected_task_id

        for item in self.tree.get_children():
            self.tree.delete(item)

        tasks = self.data.get("daily_tasks", [])
        if not tasks: return

        today_str = str(date.today())

        overdue_tasks = []
        upcoming_tasks = []

        for t in tasks:
            t_date = t.get("date", "")
            if not t_date:
                upcoming_tasks.append(t)
                continue

            if t_date < today_str and t["status"] != "done":
                overdue_tasks.append(t)
            elif t_date >= today_str or t["status"] == "done":
                if t["status"] == "done" and t_date < today_str:
                    continue
                upcoming_tasks.append(t)

        if overdue_tasks:
            overdue_label = self.txt.get("tag_overdue", "OVERDUE")
            self.tree.insert("", "end", values=("⚠", f"{overdue_label}"), tags=("overdue_header",))
            for t in overdue_tasks:
                self._insert_task_row(t)
            self.tree.insert("", "end", values=("", ""), tags=("default",))

        if upcoming_tasks:
            all_dates = sorted(list(set(t.get("date", "") for t in upcoming_tasks)))
            for day in all_dates:
                day_tasks = [t for t in upcoming_tasks if t.get("date", "") == day]
                day_tasks.sort(key=lambda x: x["status"] == "done")

                if not day_tasks: continue

                display_date = day if day else self.txt.get("lbl_no_date", "No Date")
                if day == today_str:
                    display_date += f" ({self.txt.get('tag_today', 'Today')})"

                self.tree.insert("", "end", values=("●", f"{display_date}"), tags=("header",))
                for t in day_tasks:
                    self._insert_task_row(t)
                self.tree.insert("", "end", values=("", ""), tags=("default",))

        if sel_id and self.tree.exists(sel_id):
            self.tree.selection_set(sel_id)

    def _insert_task_row(self, t):
        status_icon = "☑" if t["status"] == "done" else "☐"
        tags = []
        if t["status"] == "done":
            tags.append("done")
        else:
            col = t.get("color")
            if col:
                tag_name = f"col_{t['id']}"
                self.tree.tag_configure(tag_name, foreground=col, font=("Arial", 13, "bold"))
                tags.append(tag_name)
            else:
                tags.append("default")

        self.tree.insert("", "end", iid=t["id"],
                         values=(f"  {status_icon}", t["content"]),
                         tags=tuple(tags))

    def move_to_tomorrow(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        task = next((t for t in self.data["daily_tasks"] if t["id"] == item_id), None)
        if not task: return

        tomorrow = date.today() + timedelta(days=1)
        task["date"] = str(tomorrow)

        save(self.data)
        self.refresh_table()
        # ZMIANA: Wywołanie odświeżania statystyk
        if self.dashboard_callback: self.dashboard_callback()

    def toggle_status(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        if not any(t["id"] == item_id for t in self.data["daily_tasks"]):
            return

        for t in self.data["daily_tasks"]:
            if t["id"] == item_id:
                t["status"] = "done" if t["status"] == "todo" else "todo"
                break

        save(self.data)
        self.refresh_table()
        # ZMIANA: Wywołanie odświeżania statystyk
        if self.dashboard_callback: self.dashboard_callback()

    def delete_task(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        if not any(t["id"] == item_id for t in self.data["daily_tasks"]): return

        title = self.txt.get("btn_delete", "Delete")
        msg = self.txt.get("msg_confirm_del_task", "Delete this task?")

        if messagebox.askyesno(title, msg):
            self.data["daily_tasks"] = [t for t in self.data["daily_tasks"] if t["id"] != item_id]
            save(self.data)
            self.deselect_all()
            self.refresh_table()
            # ZMIANA: Wywołanie odświeżania statystyk
            if self.dashboard_callback: self.dashboard_callback()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()