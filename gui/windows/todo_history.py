import customtkinter as ctk
from tkinter import messagebox
from datetime import date, datetime, timedelta
import uuid


class TodoHistoryPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, close_callback=None, refresh_main_callback=None,
                 open_note_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.close_callback = close_callback
        self.refresh_main_callback = refresh_main_callback
        self.open_note_callback = open_note_callback

        # Słownik do mapowania list zadań
        self.list_names = {}

        # --- NAGŁÓWEK ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=(10, 20))

        title = self.txt.get("win_history_title", "Task History")
        ctk.CTkLabel(self.header_frame, text=title, font=("Arial", 20, "bold")).pack(side="left")

        # --- PANEL AKCJI ZBIORCZYCH ---
        self.actions_frame = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        self.actions_frame.pack(fill="x", padx=10, pady=(0, 15))

        # Kolory dla stylu "Quick Access" (outline)
        COL_ORANGE = "#e67e22"
        COL_RED = "#e74c3c"
        HOVER_BG = ("gray85", "gray30")

        # Przycisk "Przywróć zaległe"
        self.btn_restore_all = ctk.CTkButton(
            self.actions_frame,
            text=self.txt.get("btn_restore_overdue", "Restore Overdue"),
            command=self.restore_all_overdue,
            height=35,
            fg_color="transparent",
            border_width=2,
            border_color=COL_ORANGE,
            text_color=COL_ORANGE,
            hover_color=HOVER_BG,
            font=("Arial", 13, "bold")
        )
        self.btn_restore_all.pack(side="left", fill="x", padx=10, pady=(5, 5))

        # Przycisk "Wyczyść historię"
        self.btn_clear_all = ctk.CTkButton(
            self.actions_frame,
            text=self.txt.get("btn_clear_history", "Clear History"),
            command=self.clear_history,
            height=35,
            fg_color="transparent",
            border_width=2,
            border_color=COL_RED,
            text_color=COL_RED,
            hover_color=HOVER_BG,
            font=("Arial", 13, "bold")
        )
        self.btn_clear_all.pack(side="left", fill="x", padx=10, pady=(5, 5))

        # --- LISTA ZADAŃ ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.load_history()

        # --- STOPKA ---
        ctk.CTkButton(self, text=self.txt.get("btn_close", "Close"), command=self.perform_close,
                      fg_color="transparent", border_width=1, border_color="gray",
                      text_color=("gray10", "gray90")).pack(pady=10)

    def perform_close(self):
        if self.close_callback: self.close_callback()

    def load_history(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.storage: return

        # Ładujemy nazwy list
        lists_db = self.storage.get_task_lists()
        self.list_names = {l["id"]: l["name"] for l in lists_db}
        self.list_names["general"] = self.txt.get("list_general", "General")

        # Pobieramy historię
        tasks = [dict(t) for t in self.storage.get_task_history()]

        if not tasks:
            ctk.CTkLabel(self.scroll_frame, text=self.txt.get("msg_no_history", "No history found."),
                         text_color="gray", font=("Arial", 14)).pack(pady=50)
            return

        # Grupowanie
        today = date.today()
        groups = {
            "yesterday": [],
            "last_7": [],
            "older": []
        }

        for t in tasks:
            t_date_str = t.get("date", "")
            if not t_date_str:
                groups["older"].append(t)
                continue

            try:
                t_date = datetime.strptime(t_date_str, "%Y-%m-%d").date()
                delta = (today - t_date).days

                if delta == 1:
                    groups["yesterday"].append(t)
                elif 1 < delta <= 7:
                    groups["last_7"].append(t)
                else:
                    groups["older"].append(t)
            except:
                groups["older"].append(t)

        self._render_group(groups["yesterday"], self.txt.get("lbl_yesterday", "Yesterday"))
        self._render_group(groups["last_7"], self.txt.get("lbl_last_7", "Last 7 Days"))
        self._render_group(groups["older"], self.txt.get("lbl_older", "Older"))

    def _render_group(self, task_list, title):
        if not task_list: return

        ctk.CTkLabel(self.scroll_frame, text=title, font=("Arial", 12, "bold"),
                     text_color=("gray50", "gray70"), anchor="w").pack(fill="x", padx=10, pady=(15, 5))

        for t in task_list:
            self._render_row(t)

    def _render_row(self, task):
        # KARTA ZADANIA
        row = ctk.CTkFrame(self.scroll_frame, fg_color=("gray95", "gray25"), corner_radius=8)
        row.pack(fill="x", padx=5, pady=4)

        # --- CZĘŚĆ GÓRNA (IKONA + TEKST) ---
        top_section = ctk.CTkFrame(row, fg_color="transparent")
        top_section.pack(fill="x", padx=8, pady=(8, 0))

        # 1. Ikona (Status) - zakotwiczona do góry
        icon = "✓" if task["status"] == "done" else "✗"
        icon_color = "#2ecc71" if task["status"] == "done" else "#e74c3c"

        ctk.CTkLabel(top_section, text=icon, text_color=icon_color,
                     font=("Arial", 16, "bold"), width=25).pack(side="left", anchor="n", pady=(2, 0))

        # 2. Tekst Zadania (z zawijaniem)
        ctk.CTkLabel(top_section, text=task["content"], font=("Arial", 13),
                     anchor="w", justify="left", wraplength=240).pack(side="left", fill="x", expand=True, padx=5)

        # --- CZĘŚĆ DOLNA (DATA + PRZYCISKI) ---
        bottom_section = ctk.CTkFrame(row, fg_color="transparent", height=30)
        bottom_section.pack(fill="x", padx=8, pady=(5, 8))

        # Data i Nazwa Listy (po lewej, mała, szara)
        date_str = task.get("date", "")
        if not date_str:
            date_str = self.txt.get("lbl_no_date", "No Date")

        l_id = task.get("list_id")
        list_str = ""

        if l_id and l_id in self.list_names:
            list_str = f" | {self.list_names[l_id]}"
        elif l_id == "general":
            list_str = f" | {self.txt.get('list_general', 'General')}"
        elif date_str != self.txt.get("lbl_no_date", "No Date"):
            list_str = f" | {self.txt.get('list_scheduled', 'Scheduled')}"

        ctk.CTkLabel(bottom_section, text=date_str + list_str, font=("Arial", 11),
                     text_color="gray", anchor="w").pack(side="left", padx=5)

        # PRZYCISKI AKCJI (po prawej)

        # 3. Delete (Kosz)
        ctk.CTkButton(bottom_section, text="🗑", width=30, height=28, fg_color="transparent",
                      text_color="#e74c3c", hover_color=("gray85", "gray35"),
                      font=("Arial", 14),
                      command=lambda id=task["id"]: self.delete_single(id)).pack(side="right", padx=2)

        # 2. Copy (Plus)
        ctk.CTkButton(bottom_section, text="+", width=30, height=28, fg_color="transparent",
                      text_color=("gray10", "gray90"), hover_color=("gray85", "gray35"),
                      font=("Arial", 16, "bold"),
                      command=lambda t=task: self.copy_task(t)).pack(side="right", padx=2)

        # 1. Restore (Strzałka)
        ctk.CTkButton(bottom_section, text="↺", width=30, height=28, fg_color="transparent",
                      text_color=("gray10", "gray90"), hover_color=("gray85", "gray35"),
                      font=("Arial", 16, "bold"),
                      command=lambda t=task: self.restore_task(t)).pack(side="right", padx=2)

        # 0. Open Note (Ołówek) - tylko jeśli zadanie ma notatkę
        has_note = (task.get("note") or "").strip()
        if has_note and self.open_note_callback:
            ctk.CTkButton(bottom_section, text="✎", width=30, height=28, fg_color="transparent",
                          text_color=("gray10", "gray90"), hover_color=("gray85", "gray35"),
                          font=("Arial", 16, "bold"),
                          command=lambda t=task: self.open_note_callback(t)).pack(side="right", padx=2)

    def restore_task(self, task):
        task["status"] = "todo"
        task["date"] = str(date.today())
        self.storage.update_daily_task(task)
        self.load_history()
        if self.refresh_main_callback: self.refresh_main_callback()

    def copy_task(self, task):
        new_task = {
            "id": str(uuid.uuid4()),
            "content": task["content"],
            "status": "todo",
            "created_at": str(date.today()),
            "date": str(date.today()),
            "color": task.get("color"),
            "list_id": task.get("list_id")
        }
        self.storage.add_daily_task(new_task)
        if self.refresh_main_callback: self.refresh_main_callback()
        messagebox.showinfo(self.txt["msg_info"], self.txt.get("msg_task_copied", "Task copied to today!"))

    def delete_single(self, task_id):
        if messagebox.askyesno(self.txt["btn_delete"], self.txt["msg_confirm_del_task"]):
            self.storage.delete_daily_task(task_id)
            self.load_history()
            if self.refresh_main_callback: self.refresh_main_callback()

    def clear_history(self):
        if messagebox.askyesno(self.txt["msg_warning"],
                               self.txt.get("msg_confirm_clear_history", "Delete all history?")):
            self.storage.clear_task_history(str(date.today()))
            self.load_history()
            if self.refresh_main_callback: self.refresh_main_callback()

    def restore_all_overdue(self):
        count = self.storage.restore_overdue_tasks(str(date.today()))
        if count > 0:
            self.load_history()
            if self.refresh_main_callback: self.refresh_main_callback()
            messagebox.showinfo(self.txt["msg_success"], f"{count} tasks restored!")
        else:
            messagebox.showinfo(self.txt["msg_info"], "No overdue tasks found.")