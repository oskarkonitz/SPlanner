import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.colorchooser import askcolor
import customtkinter as ctk
from datetime import date, timedelta, datetime
import uuid
from tkcalendar import Calendar
from gui.windows.todo_history import TodoHistoryPanel
from gui.components.drawers import NoteDrawer


class TodoWindow:
    def __init__(self, parent, txt, btn_style, dashboard_callback, selection_callback=None, drawer_parent=None,
                 storage=None, drawer=None):
        self.parent = parent
        self.txt = txt
        self.btn_style = btn_style
        self.dashboard_callback = dashboard_callback
        self.selection_callback = selection_callback
        self.storage = storage
        self.drawer = drawer  # ZAPISUJEMY DRAWER

        draw_target = drawer_parent if drawer_parent else self.parent
        self.note_drawer = NoteDrawer(draw_target, self.txt, self.btn_style, self.save_data_from_drawer)

        self.current_list_id = "scheduled"  # Domyślny widok
        self.selected_task_id = None
        self.current_color = None

        # --- RAMKA Z BIAŁYM OBRAMOWANIEM I PADDINGIEM ---
        self.border_frame = ctk.CTkFrame(self.parent, fg_color="transparent",
                                         border_width=1, border_color=("gray70", "white"), corner_radius=2)
        self.border_frame.pack(fill="both", expand=True, padx=(0, 10), pady=8)

        # --- PANED WINDOW (UKŁAD MASTER-DETAIL) ---
        self.paned = tk.PanedWindow(
            self.border_frame,
            orient="horizontal",
            sashwidth=10,
            bg="#2b2b2b",
            bd=0,
            sashrelief="groove",
            handlesize=35,
        )
        self.paned.pack(fill="both", expand=True, padx=1, pady=(1, 2))

        # LEWY PANEL (Nawigacja List)
        self.left_panel = ctk.CTkFrame(self.paned, corner_radius=0, fg_color="transparent")
        self.paned.add(self.left_panel, minsize=200, stretch="never")

        # PRAWY PANEL (Zadania)
        self.right_panel = ctk.CTkFrame(self.paned, corner_radius=0, fg_color="transparent")
        self.paned.add(self.right_panel, minsize=400, stretch="always")

        # --- LEWY PANEL ZAWARTOŚĆ ---
        self.scroll_lists = ctk.CTkScrollableFrame(self.left_panel, fg_color="transparent")
        self.scroll_lists.pack(fill="both", expand=True, padx=5, pady=5)

        self.btn_add_list = ctk.CTkButton(self.left_panel, text=self.txt.get("btn_add_list", "+ Add List"),
                                          command=self.add_custom_list, **self.btn_style)
        self.btn_add_list.configure(fg_color="transparent", border_width=1, border_color="gray",
                                    text_color=("gray10", "gray90"))
        self.btn_add_list.pack(pady=10, padx=10, fill="x")

        # --- PRAWY PANEL ZAWARTOŚĆ ---
        self.lbl_list_title = ctk.CTkLabel(self.right_panel, text=self.txt.get("list_scheduled", "Scheduled"),
                                           font=("Arial", 20, "bold"))
        self.lbl_list_title.pack(anchor="w", padx=15, pady=(10, 0))

        # --- GÓRNY PASEK (WPROWADZANIE DANYCH) ---
        self.top_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=10, pady=(5, 5))

        # Pole Zadania
        placeholder = self.txt.get("todo_placeholder", "Enter task...")
        self.entry_task = ctk.CTkEntry(self.top_frame, placeholder_text=placeholder, height=35)
        self.entry_task.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Data (Ramka)
        self.date_frame = ctk.CTkFrame(self.top_frame, fg_color="transparent")
        self.date_frame.pack(side="left", padx=(0, 5))

        self.entry_date = ctk.CTkEntry(self.date_frame, width=100, height=35, justify="center")
        self.entry_date.insert(0, str(date.today()))
        self.entry_date.pack(side="left", padx=(0, 2))

        self.btn_cal = ctk.CTkButton(self.date_frame, text="📅", width=35,
                                     command=self.open_calendar_popup,
                                     **self.btn_style)
        self.btn_cal.pack(side="left")

        self.btn_history = ctk.CTkButton(self.top_frame, text="🕒", width=35, height=35,
                                         fg_color="transparent", border_width=1, border_color="gray",
                                         text_color=("gray10", "gray90"),
                                         command=self.open_history)
        self.btn_history.pack(side="left", padx=(5, 5))

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
        self.table_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=5, pady=8)

        columns = ("status", "task")
        self.tree = ttk.Treeview(self.table_frame, columns=columns, show="tree", selectmode="browse")
        self.tree.column("#0", width=0, stretch=False)

        self.tree.heading("status", text=self.txt.get("col_status", "Status"))
        self.tree.column("status", width=60, anchor="e", stretch=False)

        self.tree.heading("task", text=self.txt.get("col_task", "Task"))
        self.tree.column("task", width=500, anchor="w")

        # Style
        self.tree.tag_configure("done", foreground="#00b800", font=("Arial", 13, "bold"))
        self.tree.tag_configure("header", font=("Arial", 13, "bold"), foreground="#e6b800")
        self.tree.tag_configure("default", font=("Arial", 13, "bold"))
        self.tree.tag_configure("overdue_header", foreground="#e74c3c", font=("Arial", 13, "bold"))
        self.tree.tag_configure("overdue_item", font=("Arial", 13, "bold"))
        self.tree.tag_configure("today_color", font=("Arial", 13, "bold"), foreground="violet")

        scrollbar = ctk.CTkScrollbar(self.table_frame, orientation="vertical", command=self.tree.yview,
                                     fg_color="transparent", bg_color="transparent")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.tree.pack(side="left", fill="both", expand=True)

        self.lbl_empty = ctk.CTkLabel(self.table_frame,
                                      text=self.txt.get("msg_empty_todo", "No tasks."),
                                      font=("Arial", 16, "bold"),
                                      text_color="gray")

        self.tree.bind("<Double-1>", self.on_double_click)
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

        self.refresh_lists()
        self.refresh_table()

    # --- LOGIKA LIST ZADAŃ ---
    def refresh_lists(self):
        for widget in self.scroll_lists.winfo_children():
            widget.destroy()

        if not self.storage: return

        # Obliczanie ilości zadań
        all_tasks = [dict(t) for t in self.storage.get_daily_tasks()]
        counts = {"scheduled": 0, "general": 0}
        custom_counts = {}

        for t in all_tasks:
            if t["status"] == "done": continue
            lid = t.get("list_id")
            if t.get("date", "") != "":
                counts["scheduled"] += 1
            if t.get("date", "") == "" and (lid is None or lid == "general"):
                counts["general"] += 1
            if lid and lid not in ["general", "scheduled"]:
                custom_counts[lid] = custom_counts.get(lid, 0) + 1

        # SYSTEMOWE
        ctk.CTkLabel(self.scroll_lists, text=self.txt.get("lbl_sys_lists", "System Lists"), font=("Arial", 12, "bold"),
                     text_color="gray").pack(anchor="w", pady=(5, 2))

        self.create_list_btn("scheduled", self.txt.get("list_scheduled", "Scheduled"), counts["scheduled"])
        self.create_list_btn("general", self.txt.get("list_general", "General"), counts["general"])

        # UŻYTKOWNIKA
        custom_lists = self.storage.get_task_lists()
        if custom_lists:
            ctk.CTkLabel(self.scroll_lists, text=self.txt.get("lbl_my_lists", "My Lists"), font=("Arial", 12, "bold"),
                         text_color="gray").pack(anchor="w", pady=(15, 2))

            for lst in custom_lists:
                c = custom_counts.get(lst["id"], 0)
                self.create_list_btn(lst["id"], lst["name"], c)
        self.parent.after(100, self._force_scroll_redraw)

    def _force_scroll_redraw(self):
        """Wymusza odświeżenie warstwy Canvas w lewym panelu list."""
        try:
            self.parent.update_idletasks()
            # Pociągamy za niewidzialny sznurek scrolla w lewym panelu
            self.scroll_lists._parent_canvas.yview_scroll(1, "units")
            self.scroll_lists._parent_canvas.yview_scroll(-1, "units")
        except Exception:
            pass

    def create_list_btn(self, list_id, list_name, count):
        is_active = (self.current_list_id == list_id)
        bg_color = ("gray75", "gray25") if is_active else "transparent"
        text_color = ("black", "white") if is_active else ("gray20", "gray80")

        display_text = f"{list_name}  ({count})" if count > 0 else list_name

        btn = ctk.CTkButton(self.scroll_lists, text=display_text, fg_color=bg_color, text_color=text_color,
                            anchor="w", height=32, command=lambda: self.select_list(list_id, list_name))
        btn.pack(fill="x", pady=1)

        # Menu kontekstowe (Usuwanie listy customowej)
        if list_id not in ["scheduled", "general"]:
            if self.parent.tk.call('tk', 'windowingsystem') == 'aqua':
                btn.bind("<Button-2>", lambda e: self.show_list_menu(e, list_id))
            else:
                btn.bind("<Button-3>", lambda e: self.show_list_menu(e, list_id))

    def select_list(self, list_id, list_name):
        self.current_list_id = list_id
        self.lbl_list_title.configure(text=list_name)

        if list_id == "general":
            self.date_frame.pack_forget()
            self.entry_date.delete(0, "end")
        elif list_id == "scheduled":
            self.date_frame.pack(side="left", padx=(0, 5), after=self.entry_task)
            self.entry_date.delete(0, "end")
            self.entry_date.insert(0, str(date.today()))
        else:
            self.date_frame.pack(side="left", padx=(0, 5), after=self.entry_task)
            self.entry_date.delete(0, "end")

        self.refresh_lists()
        self.refresh_table()

    def add_custom_list(self):
        dialog = ctk.CTkInputDialog(text=self.txt.get("form_list_name", "List Name:"),
                                    title=self.txt.get("win_add_list", "Add New List"))
        name = dialog.get_input()
        if name:
            new_list = {"id": f"list_{uuid.uuid4().hex[:8]}", "name": name, "icon": ""}
            if self.storage:
                self.storage.add_task_list(new_list)
            self.refresh_lists()

    def show_list_menu(self, event, list_id):
        menu = tk.Menu(self.parent, tearoff=0)
        menu.add_command(label=self.txt.get("btn_delete", "Delete"), command=lambda: self.delete_list(list_id))
        menu.tk_popup(event.x_root, event.y_root)

    def delete_list(self, list_id):
        if messagebox.askyesno(self.txt.get("btn_delete", "Delete"),
                               self.txt.get("msg_confirm_del_list", "Delete this list and ALL tasks inside it?")):
            if self.storage:
                self.storage.delete_task_list(list_id)
            if self.current_list_id == list_id:
                self.select_list("scheduled", self.txt.get("list_scheduled", "Scheduled"))
            else:
                self.refresh_lists()
                self.refresh_table()
            if self.dashboard_callback: self.dashboard_callback()

    # --- LOGIKA OGÓLNA ---
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
        date_val = self.entry_date.get().strip() if self.date_frame.winfo_ismapped() else ""

        if not content: return

        # Logika przydzielania Listy i Daty
        if self.current_list_id == "scheduled":
            if not date_val: date_val = str(date.today())
            list_id = None
        elif self.current_list_id == "general":
            date_val = ""
            list_id = "general"
        else:
            list_id = self.current_list_id

        if self.selected_task_id:
            # EDYCJA
            target_task = self.storage.get_daily_task(self.selected_task_id)
            if target_task:
                target_task["content"] = content
                target_task["date"] = date_val
                target_task["color"] = self.current_color
                # Celowo nie ruszamy list_id aby przy edycji nie wywalało zadania z listy do innej
                if self.storage:
                    self.storage.update_daily_task(target_task)

            self.deselect_all()
        else:
            # NOWE ZADANIE
            new_task = {
                "id": str(uuid.uuid4()),
                "content": content,
                "status": "todo",
                "created_at": str(date.today()),
                "date": date_val,
                "color": self.current_color,
                "note": "",
                "list_id": list_id
            }

            if self.storage:
                self.storage.add_daily_task(new_task)

            self.entry_task.delete(0, "end")
            self.current_color = None
            self.btn_color.configure(fg_color="transparent")

        self.refresh_table()
        self.refresh_lists()
        if self.dashboard_callback: self.dashboard_callback()

    def on_select(self, event):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        task = self.storage.get_daily_task(item_id)

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

            if self.selection_callback:
                if task["status"] == "done":
                    self.selection_callback("todo_restore", "todo_delete", "disabled")
                else:
                    self.selection_callback("todo_complete", "todo_delete", "disabled")
        else:
            if self.selection_callback:
                self.selection_callback("idle", "idle", "idle")
            self.selected_task_id = None
            self.btn_action.configure(text="+")

    def deselect_all(self):
        selection = self.tree.selection()
        if selection:
            self.tree.selection_remove(selection)
        self.selected_task_id = None

        if hasattr(self, 'note_drawer') and self.note_drawer.is_open:
            self.note_drawer.close_panel()

        self.entry_task.delete(0, "end")
        self.entry_date.delete(0, "end")

        if self.current_list_id == "scheduled":
            self.entry_date.insert(0, str(date.today()))

        self.current_color = None
        self.btn_color.configure(fg_color="transparent")
        self.btn_action.configure(text="+")
        self.parent.focus_set()

        if self.selection_callback:
            self.selection_callback("idle", "idle", "idle")

    def on_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            self.deselect_all()
        else:
            task = self.storage.get_daily_task(item)
            if not task:
                self.deselect_all()

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        task = self.storage.get_daily_task(item_id)
        if task:
            self.note_drawer.load_note(task, task["content"])

    def save_data_from_drawer(self, is_new_note=False):
        if self.storage and self.note_drawer.current_item_data:
            # --- POPRAWKA: Bezpieczne zwiększanie licznika statystyk ---
            if is_new_note:
                stats = self.storage.get_global_stats()
                raw_val = stats.get("notes_added", 0)

                # Obsługa błędu typu (String vs Int) przy pobieraniu z Supabase
                try:
                    curr = int(raw_val)
                except (ValueError, TypeError):
                    curr = 0

                self.storage.update_global_stat("notes_added", curr + 1)

            # Zapisanie samej treści zadania/notatki w bazie danych
            item = self.note_drawer.current_item_data
            self.storage.update_daily_task(item)

        # Odświeżenie widoku i dashboardu
        self.refresh_table()
        if self.dashboard_callback: self.dashboard_callback()

    def refresh_table(self):
        if not self.storage:
            return

        tasks = [dict(t) for t in self.storage.get_daily_tasks()]
        filtered_tasks = []

        # --- FILTROWANIE KONTEKSTOWE ---
        for t in tasks:
            lid = t.get("list_id")
            t_date = t.get("date", "")

            if self.current_list_id == "scheduled":
                if t_date == "": continue
            elif self.current_list_id == "general":
                if t_date != "" or (lid is not None and lid != "general"): continue
            else:
                if lid != self.current_list_id: continue

            filtered_tasks.append(t)

        sel_id = self.selected_task_id

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree.insert("", "end", values=("", ""), tags=("default",))

        if not filtered_tasks:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_empty.lift()
            return

        today_str = str(date.today())

        overdue_tasks = []
        upcoming_tasks = []

        for t in filtered_tasks:
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

        # --- RYSOWANIE TABELI ---

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

                if self.current_list_id != "general":
                    display_date = day if day else self.txt.get("lbl_no_date", "No Date")
                    if day == today_str:
                        display_date += f" ({self.txt.get('tag_today', 'Today')})"
                        self.tree.insert("", "end", values=("●", f"{display_date}"), tags=("today_color",))
                    else:
                        self.tree.insert("", "end", values=("●", f"{display_date}"), tags=("header",))

                for t in day_tasks:
                    self._insert_task_row(t)

                if self.current_list_id != "general":
                    self.tree.insert("", "end", values=("", ""), tags=("default",))

        if sel_id and self.tree.exists(sel_id):
            self.tree.selection_set(sel_id)

        if not overdue_tasks and not upcoming_tasks:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_empty.lift()
        else:
            self.lbl_empty.place_forget()

    def _insert_task_row(self, t):
        status_icon = " ☑" if t["status"] == "done" else " ☐"
        has_note = (t.get("note") or "").strip()
        marks = "✎" if has_note else ""

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
                         values=(f"  {marks}{status_icon}", t["content"]),
                         tags=tuple(tags))

    def move_to_tomorrow(self):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        task = self.storage.get_daily_task(item_id)
        if not task: return

        tomorrow = date.today() + timedelta(days=1)
        task["date"] = str(tomorrow)

        if self.storage:
            self.storage.update_daily_task(task)

        self.refresh_table()
        self.refresh_lists()
        if self.dashboard_callback: self.dashboard_callback()

    def toggle_status(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        target_task = self.storage.get_daily_task(item_id)

        if target_task:
            target_task["status"] = "done" if target_task["status"] == "todo" else "todo"
            if self.storage:
                self.storage.update_daily_task(target_task)

        self.refresh_table()
        self.refresh_lists()
        if self.dashboard_callback: self.dashboard_callback()

    def delete_task(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        item_id = selected[0]

        if not self.storage.get_daily_task(item_id): return

        title = self.txt.get("btn_delete", "Delete")
        msg = self.txt.get("msg_confirm_del_task", "Delete this task?")

        if messagebox.askyesno(title, msg):
            if self.storage:
                self.storage.delete_daily_task(item_id)

            self.deselect_all()
            self.refresh_table()
            self.refresh_lists()
            if self.dashboard_callback: self.dashboard_callback()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def open_note_from_history(self, task):
        if hasattr(self, 'note_drawer'):
            self.note_drawer.load_note(task, task["content"])

    def open_history(self):
        if self.drawer:
            self.drawer.set_content(
                TodoHistoryPanel,
                txt=self.txt,
                btn_style=self.btn_style,
                storage=self.storage,
                close_callback=self.drawer.close_panel,
                refresh_main_callback=lambda: [self.refresh_table(), self.refresh_lists(), self.dashboard_callback()],
                open_note_callback=self.open_note_from_history
            )
        else:
            messagebox.showinfo("Info", "Drawer not available in this view context.")