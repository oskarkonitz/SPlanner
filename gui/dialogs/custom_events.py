import tkinter as tk
from tkinter import messagebox, colorchooser
import customtkinter as ctk
from tkcalendar import DateEntry
import uuid
from datetime import date, timedelta, datetime


class ManageListsPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, refresh_callback=None, close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.refresh_callback = refresh_callback
        self.close_callback = close_callback

        self.editing_id = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text=self.txt.get("win_manage_lists", "Manage Event Lists"),
                     font=("Arial", 20, "bold")).pack(side="left")

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="x", pady=10)

        self.name_var = tk.StringVar()
        self.color_var = tk.StringVar(value="#e67e22")

        ctk.CTkEntry(self.form_frame, textvariable=self.name_var, placeholder_text="Name (e.g. Work)").pack(side="left",
                                                                                                            fill="x",
                                                                                                            expand=True,
                                                                                                            padx=(10,
                                                                                                                  5),
                                                                                                            pady=10)

        self.btn_color = ctk.CTkButton(self.form_frame, text="", width=30, fg_color=self.color_var.get(),
                                       hover_color=self.color_var.get(), command=self.pick_color, corner_radius=6)
        self.btn_color.pack(side="left", padx=5, pady=10)

        self.btn_action = ctk.CTkButton(self.form_frame, text="Add", width=60, command=self.save_list, **self.btn_style)
        self.btn_action.pack(side="left", padx=(5, 5), pady=10)

        self.btn_cancel_edit = ctk.CTkButton(self.form_frame, text="Cancel", width=60, command=self.cancel_edit,
                                             fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

        self.list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, pady=10)
        self.load_lists()

        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=20, side="bottom")
        ctk.CTkButton(footer, text=self.txt.get("btn_close", "Close"), command=self.close_panel,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    fill="x",
                                                                                                    expand=True)

    def pick_color(self):
        color_code = colorchooser.askcolor(title="Choose color", initialcolor=self.color_var.get())[1]
        if color_code:
            self.color_var.set(color_code)
            self.btn_color.configure(fg_color=color_code, hover_color=color_code)

    def close_panel(self):
        if self.close_callback:
            self.close_callback()

    def load_lists(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        lists = self.storage.get_event_lists()
        if not lists:
            ctk.CTkLabel(self.list_frame, text="No lists added yet.", text_color="gray").pack(pady=20)
            return

        for lst in lists:
            row = ctk.CTkFrame(self.list_frame, fg_color=("gray85", "gray25"), corner_radius=8)
            row.pack(fill="x", pady=5)

            color_lbl = ctk.CTkLabel(row, text="■", text_color=lst.get("color", "#3498db"), font=("Arial", 20))
            color_lbl.pack(side="left", padx=10)

            ctk.CTkLabel(row, text=lst["name"], font=("Arial", 14, "bold")).pack(side="left", padx=5)

            ctk.CTkButton(row, text="Delete", width=60, fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda id=lst["id"]: self.delete_list(id)).pack(side="right", padx=(5, 10), pady=5)

            ctk.CTkButton(row, text="Edit", width=60, fg_color=("gray70", "gray40"), text_color=("black", "white"),
                          hover_color=("gray60", "gray50"),
                          command=lambda l=lst: self.start_edit(l)).pack(side="right", padx=5, pady=5)

    def start_edit(self, lst):
        self.editing_id = lst["id"]
        self.name_var.set(lst["name"])
        self.color_var.set(lst.get("color", "#3498db"))
        self.btn_color.configure(fg_color=self.color_var.get(), hover_color=self.color_var.get())

        self.btn_action.configure(text="Save")
        self.btn_cancel_edit.pack(side="left", padx=(0, 10), pady=10)

    def cancel_edit(self):
        self.editing_id = None
        self.name_var.set("")
        self.color_var.set("#e67e22")
        self.btn_color.configure(fg_color=self.color_var.get(), hover_color=self.color_var.get())

        self.btn_action.configure(text="Add")
        self.btn_cancel_edit.pack_forget()

    def save_list(self):
        name = self.name_var.get().strip()
        color = self.color_var.get().strip()
        if name:
            list_id = self.editing_id if self.editing_id else f"evlist_{uuid.uuid4().hex[:8]}"
            self.storage.add_event_list({"id": list_id, "name": name, "color": color})

            self.cancel_edit()
            self.load_lists()
            if self.refresh_callback: self.refresh_callback()

    def delete_list(self, lst_id):
        if messagebox.askyesno(self.txt.get("msg_warning", "Confirm"), "Delete this list?"):
            self.storage.delete_event_list(lst_id)
            if self.editing_id == lst_id:
                self.cancel_edit()
            self.load_lists()
            if self.refresh_callback: self.refresh_callback()


class AddCustomEventPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, refresh_callback=None, close_callback=None, event_data=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.refresh_callback = refresh_callback
        self.close_callback = close_callback

        # NOWOŚĆ: Pamiętamy edytowane dane
        self.event_data = event_data

        self.event_lists = self.storage.get_event_lists()
        self.list_names = ["None (Standalone)"] + [l["name"] for l in self.event_lists]

        # --- NAGŁÓWEK ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        title_text = "Edit Event" if self.event_data else "Add Event"
        ctk.CTkLabel(header, text=self.txt.get("win_add_event", title_text), font=("Arial", 20, "bold")).pack(
            side="left")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True)

        ctk.CTkLabel(content, text="Event Title:", font=("Arial", 14, "bold")).pack(anchor="w")
        self.title_var = tk.StringVar()
        ctk.CTkEntry(content, textvariable=self.title_var, placeholder_text="e.g. Morning Shift").pack(fill="x",
                                                                                                       pady=(5, 15))

        ctk.CTkLabel(content, text="Category / List:", font=("Arial", 14, "bold")).pack(anchor="w")
        self.list_var = tk.StringVar(value="None (Standalone)")
        ctk.CTkOptionMenu(content, variable=self.list_var, values=self.list_names).pack(fill="x", pady=(5, 20))

        self.is_recurring_var = tk.BooleanVar(value=False)
        ctk.CTkSwitch(content, text="Repeats Weekly?", variable=self.is_recurring_var, command=self.toggle_recurring,
                      font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 15))

        self.date_frame = ctk.CTkFrame(content, fg_color=("gray90", "gray15"), corner_radius=8)
        self.date_frame.pack(fill="x", pady=5)

        # Puste zmienne dla build_date_frame
        self.day_var = tk.StringVar(value="Monday")

        time_frame = ctk.CTkFrame(content, fg_color="transparent")
        time_frame.pack(fill="x", pady=20)

        ctk.CTkLabel(time_frame, text="Start Time:", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w",
                                                                                      padx=5)
        self.start_time_var = tk.StringVar(value="14:00")
        ctk.CTkEntry(time_frame, textvariable=self.start_time_var, width=80).grid(row=0, column=1, padx=5)

        ctk.CTkLabel(time_frame, text="End Time:", font=("Arial", 14, "bold")).grid(row=0, column=2, sticky="w",
                                                                                    padx=(20, 5))
        self.end_time_var = tk.StringVar(value="16:00")
        ctk.CTkEntry(time_frame, textvariable=self.end_time_var, width=80).grid(row=0, column=3, padx=5)

        # --- UZUPEŁNIANIE DANYCH (EDYCJA) ---
        if self.event_data:
            self.title_var.set(self.event_data.get("title", ""))
            self.start_time_var.set(self.event_data.get("start_time", "14:00"))
            self.end_time_var.set(self.event_data.get("end_time", "16:00"))

            l_id = self.event_data.get("list_id")
            if l_id:
                for lst in self.event_lists:
                    if lst["id"] == l_id:
                        self.list_var.set(lst["name"])
                        break

            self.is_recurring_var.set(self.event_data.get("is_recurring", False))

        # Budujemy ramkę z kalendarzami bazując na `is_recurring_var`
        self.build_date_frame()

        # Reszta uzupełniania dat po zbudowaniu widżetów
        if self.event_data:
            if self.event_data.get("is_recurring"):
                day_idx = self.event_data.get("day_of_week", 0)
                days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                if 0 <= day_idx < 7: self.day_var.set(days[day_idx])

                if s_date := self.event_data.get("start_date"):
                    try:
                        self.cal_start.set_date(datetime.strptime(s_date, "%Y-%m-%d").date())
                    except:
                        pass
                if e_date := self.event_data.get("end_date"):
                    try:
                        self.cal_end.set_date(datetime.strptime(e_date, "%Y-%m-%d").date())
                    except:
                        pass
            else:
                if d_str := self.event_data.get("date"):
                    try:
                        self.cal_single.set_date(datetime.strptime(d_str, "%Y-%m-%d").date())
                    except:
                        pass

        # --- STOPKA Z PRZYCISKAMI ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=20, side="bottom")

        ctk.CTkButton(footer, text=self.txt.get("btn_cancel", "Cancel"), command=self.close_panel,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="left",
                                                                                                    padx=10, fill="x",
                                                                                                    expand=True)
        btn_save_text = "Save Changes" if self.event_data else "Save Event"
        ctk.CTkButton(footer, text=self.txt.get("btn_save", btn_save_text), command=self.save_event,
                      **self.btn_style).pack(side="right", padx=10, fill="x", expand=True)

    def close_panel(self):
        if self.close_callback:
            self.close_callback()

    def build_date_frame(self):
        for w in self.date_frame.winfo_children(): w.destroy()

        if self.is_recurring_var.get():
            ctk.CTkLabel(self.date_frame, text="Day of Week:").grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            ctk.CTkOptionMenu(self.date_frame, variable=self.day_var, values=days).grid(row=0, column=1, padx=15,
                                                                                        pady=(15, 5), sticky="ew")

            ctk.CTkLabel(self.date_frame, text="Valid From:").grid(row=1, column=0, padx=15, pady=5, sticky="w")
            self.cal_start = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white',
                                       borderwidth=2, date_pattern='yyyy-mm-dd')
            self.cal_start.grid(row=1, column=1, padx=15, pady=5, sticky="ew")

            ctk.CTkLabel(self.date_frame, text="Valid Until:").grid(row=2, column=0, padx=15, pady=(5, 15), sticky="w")
            self.cal_end = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white',
                                     borderwidth=2, date_pattern='yyyy-mm-dd')
            self.cal_end.grid(row=2, column=1, padx=15, pady=(5, 15), sticky="ew")

            if not self.event_data:
                self.cal_end.set_date(date.today() + timedelta(days=90))

            self.date_frame.grid_columnconfigure(1, weight=1)

        else:
            ctk.CTkLabel(self.date_frame, text="Specific Date:").pack(side="left", padx=15, pady=15)
            self.cal_single = DateEntry(self.date_frame, width=12, background='darkblue', foreground='white',
                                        borderwidth=2, date_pattern='yyyy-mm-dd')
            self.cal_single.pack(side="right", padx=15, pady=15, expand=True, fill="x")

    def toggle_recurring(self):
        self.build_date_frame()

    def save_event(self):
        title = self.title_var.get().strip() or "Event"
        is_rec = self.is_recurring_var.get()
        s_time = self.start_time_var.get()
        e_time = self.end_time_var.get()

        l_name = self.list_var.get()
        l_id = None
        color = "#3498db"
        for lst in self.event_lists:
            if lst["name"] == l_name:
                l_id = lst["id"]
                color = lst.get("color", color)
                break

        # Używamy ID z edycji lub robimy nowe
        ev_id = self.event_data["id"] if self.event_data else f"ev_{uuid.uuid4().hex[:8]}"
        ev_dict = {
            "id": ev_id,
            "title": title,
            "is_recurring": is_rec,
            "start_time": s_time,
            "end_time": e_time,
            "color": color
        }

        if l_id:
            ev_dict["list_id"] = l_id

        if is_rec:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            ev_dict["day_of_week"] = days.index(self.day_var.get())
            ev_dict["start_date"] = str(self.cal_start.get_date())
            ev_dict["end_date"] = str(self.cal_end.get_date())
        else:
            ev_dict["date"] = str(self.cal_single.get_date())

        self.storage.add_custom_event(ev_dict)
        if self.refresh_callback: self.refresh_callback()
        self.close_panel()


# ==========================================
# NOWOŚĆ: PANEL DO ZARZĄDZANIA WYDARZENIAMI
# ==========================================
class ManageEventsPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, refresh_callback=None, close_callback=None, drawer=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.refresh_callback = refresh_callback
        self.close_callback = close_callback
        self.drawer = drawer

        # --- NAGŁÓWEK ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text=self.txt.get("win_manage_events", "Manage Events"), font=("Arial", 20, "bold")).pack(
            side="left")

        # --- LISTA UTWORZONYCH WYDARZEŃ ---
        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True, pady=10)
        self.load_events()

        # --- PRZYCISK ZAMYKANIA ---
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", pady=20, side="bottom")
        ctk.CTkButton(footer, text=self.txt.get("btn_close", "Close"), command=self.close_panel,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    fill="x",
                                                                                                    expand=True)

    def close_panel(self):
        if self.close_callback:
            self.close_callback()

    def load_events(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        events = self.storage.get_custom_events()
        if not events:
            ctk.CTkLabel(self.list_frame, text="No events added yet.", text_color="gray").pack(pady=20)
            return

        for ev in events:
            row = ctk.CTkFrame(self.list_frame, fg_color=("gray85", "gray25"), corner_radius=8)
            row.pack(fill="x", pady=5)

            color_lbl = ctk.CTkLabel(row, text="■", text_color=ev.get("color", "#3498db"), font=("Arial", 20))
            color_lbl.pack(side="left", padx=10)

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

            ctk.CTkLabel(info_frame, text=ev["title"], font=("Arial", 14, "bold"), anchor="w").pack(fill="x")

            times_txt = f"{ev.get('start_time', '')} - {ev.get('end_time', '')}"
            if ev.get("is_recurring"):
                days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                d_idx = ev.get("day_of_week", 0)
                d_name = days[d_idx] if 0 <= d_idx < 7 else ""
                times_txt += f" | {d_name} (Weekly)"
            else:
                times_txt += f" | {ev.get('date', '')}"

            ctk.CTkLabel(info_frame, text=times_txt, font=("Arial", 11), text_color="gray", anchor="w").pack(fill="x")

            # Przyciski akcji
            ctk.CTkButton(row, text="Delete", width=50, fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda id=ev["id"]: self.delete_event(id)).pack(side="right", padx=(5, 10), pady=10)

            ctk.CTkButton(row, text="Edit", width=50, fg_color=("gray70", "gray40"), text_color=("black", "white"),
                          hover_color=("gray60", "gray50"),
                          command=lambda e_data=ev: self.edit_event(e_data)).pack(side="right", padx=5, pady=10)

    def edit_event(self, ev_data):
        if self.drawer:
            # Płynnie podmieniamy zawartość szuflady na formularz, przekazując mu dane o wydarzeniu
            self.drawer.set_content(AddCustomEventPanel, txt=self.txt, btn_style=self.btn_style, storage=self.storage,
                                    refresh_callback=self.refresh_callback, close_callback=self.drawer.close_panel,
                                    event_data=ev_data)

    def delete_event(self, ev_id):
        if messagebox.askyesno(self.txt.get("msg_warning", "Confirm"), "Delete this event?"):
            self.storage.delete_custom_event(ev_id)
            self.load_events()
            if self.refresh_callback: self.refresh_callback()