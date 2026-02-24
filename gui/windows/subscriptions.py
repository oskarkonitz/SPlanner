import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import date, datetime
import calendar


class SubscriptionsPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, close_callback=None, drawer=None):
        super().__init__(parent, fg_color="transparent")

        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.close_callback = close_callback
        self.drawer = drawer

        self.search_var = tk.StringVar()
        self.show_inactive_var = tk.BooleanVar(value=False)
        self.sort_var = tk.StringVar(value=self.txt.get("sort_payment", "Następna płatność"))

        self.subjects_cache = {s["id"]: s["name"] for s in self.storage.get_subjects()}

        # Słownik do przechowywania wartości dla obu stanów (dni vs data)
        self.row_display_data = {}

        # --- GÓRNY PASEK ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=10, pady=(10, 5))

        if self.close_callback:
            ctk.CTkButton(self.top_frame, text="<", width=30, height=30,
                          fg_color="transparent", border_width=1, border_color="gray",
                          text_color=("gray10", "gray90"),
                          command=self.close_callback).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(self.top_frame, text=self.txt.get("sub_title", "Zarządzaj Subskrypcjami"),
                     font=("Arial", 20, "bold")).pack(side="left")

        self.btn_add = ctk.CTkButton(self.top_frame, text=self.txt.get("btn_add_sub", "+ Dodaj Subskrypcję"),
                                     command=self.open_add_panel, **self.btn_style)
        self.btn_add.pack(side="right", padx=5)

        self.entry_search = ctk.CTkEntry(self.top_frame, textvariable=self.search_var,
                                         placeholder_text=self.txt.get("search_placeholder",
                                                                       "Szukaj nazwy/dostawcy..."),
                                         width=200)
        self.entry_search.pack(side="right", padx=10)
        self.entry_search.bind("<KeyRelease>", lambda e: self.refresh_table())

        # Opcje sortowania
        sort_opts = [
            self.txt.get("sort_payment", "Następna płatność"),
            self.txt.get("sort_expiry", "Data wygaśnięcia"),
            self.txt.get("sort_name", "Nazwa"),
            self.txt.get("sort_cost", "Koszt")
        ]
        self.cb_sort = ctk.CTkComboBox(self.top_frame, values=sort_opts, variable=self.sort_var,
                                       command=lambda x: self.refresh_table(), width=140)
        self.cb_sort.pack(side="right", padx=5)
        ctk.CTkLabel(self.top_frame, text=self.txt.get("sort_by", "Sortuj:")).pack(side="right")

        self.chk_inactive = ctk.CTkCheckBox(self.top_frame, text=self.txt.get("sub_show_inactive", "Pokaż Nieaktywne"),
                                            variable=self.show_inactive_var, command=self.refresh_table)
        self.chk_inactive.pack(side="right", padx=15)

        # --- RAMKA GŁÓWNA ---
        self.border_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.border_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- TABELA ---
        columns = ("status", "name", "provider", "cost", "next_payment", "expiry")
        self.tree = ttk.Treeview(self.border_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("status", text="")
        self.tree.column("status", width=30, anchor="center", stretch=False)

        self.tree.heading("name", text=self.txt.get("sub_name", "Nazwa"))
        self.tree.column("name", width=180, anchor="w")

        self.tree.heading("provider", text=self.txt.get("sub_provider", "Dostawca"))
        self.tree.column("provider", width=130, anchor="w")

        self.tree.heading("cost", text=self.txt.get("sub_cost", "Koszt"))
        self.tree.column("cost", width=90, anchor="center")

        # Nowa połączona kolumna Płatności
        self.tree.heading("next_payment", text=self.txt.get("sub_next_payment", "Następna płatność"))
        self.tree.column("next_payment", width=130, anchor="center")

        # Nowa połączona kolumna Wygaśnięcia
        self.tree.heading("expiry", text=self.txt.get("sub_expiry", "Wygaśnięcie"))
        self.tree.column("expiry", width=130, anchor="center")

        self.tree.tag_configure("active_normal", font=("Arial", 12))
        self.tree.tag_configure("active_warning", font=("Arial", 12, "bold"), foreground="orange")
        self.tree.tag_configure("active_danger", font=("Arial", 12, "bold"), foreground="#e74c3c")
        self.tree.tag_configure("inactive", font=("Arial", 12, "italic"), foreground="gray")

        scrollbar = ctk.CTkScrollbar(self.border_frame, orientation="vertical", command=self.tree.yview,
                                     fg_color="transparent", bg_color="transparent")
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(2, 0))
        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        self.lbl_empty = ctk.CTkLabel(self.border_frame,
                                      text=self.txt.get("msg_empty_subs", "Brak subskrypcji."),
                                      font=("Arial", 16, "bold"),
                                      text_color="gray",
                                      fg_color="transparent")

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Delete>", self.delete_selected)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label=self.txt.get("btn_edit", "Edytuj"), command=self.edit_selected)
        self.context_menu.add_command(label=self.txt.get("btn_toggle_active", "Włącz / Wyłącz"),
                                      command=self.toggle_active)
        self.context_menu.add_separator()
        self.context_menu.add_command(label=self.txt.get("btn_delete", "Usuń"), command=self.delete_selected)

        if self.tk.call('tk', 'windowingsystem') == 'aqua':
            self.tree.bind("<Button-2>", self.show_context_menu)
        else:
            self.tree.bind("<Button-3>", self.show_context_menu)

        self.refresh_table()

    def _auto_renew_billing(self, sub, today):
        """Automatycznie przesuwa datę płatności, jeśli ta już minęła."""
        b_date_str = sub.get("billing_date")
        if not b_date_str: return

        cycle = sub.get("billing_cycle")
        if cycle not in ["monthly", "yearly"]: return

        try:
            b_date = datetime.strptime(b_date_str, "%Y-%m-%d").date()
            changed = False

            while b_date < today:
                if cycle == "monthly":
                    month = b_date.month
                    year = b_date.year
                    if month == 12:
                        month = 1
                        year += 1
                    else:
                        month += 1

                    max_day = calendar.monthrange(year, month)[1]
                    day = min(b_date.day, max_day)
                    b_date = date(year, month, day)
                    changed = True
                elif cycle == "yearly":
                    try:
                        b_date = b_date.replace(year=b_date.year + 1)
                    except ValueError:  # Rok przestępny (29 lutego)
                        b_date = b_date.replace(year=b_date.year + 1, day=28)
                    changed = True

            if changed:
                sub["billing_date"] = str(b_date)
                self.storage.update_subscription(sub)
        except Exception:
            pass

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        subs = self.storage.get_subscriptions()
        search_term = self.search_var.get().lower().strip()
        show_inactive = self.show_inactive_var.get()

        today = date.today()
        self.row_display_data = {}
        filtered_subs = []

        # Przetwarzanie odnawiania i filtrowanie
        for sub in subs:
            self._auto_renew_billing(sub, today)

            is_active = sub.get("is_active", True)
            if not show_inactive and not is_active: continue

            if search_term:
                searchable = f"{sub.get('name', '')} {sub.get('provider', '')} {sub.get('note', '')}".lower()
                if search_term not in searchable: continue

            filtered_subs.append(sub)

        # Sortowanie
        sort_val = self.sort_var.get()
        if sort_val == self.txt.get("sort_name", "Nazwa"):
            filtered_subs.sort(key=lambda x: x.get("name", "").lower())
        elif sort_val == self.txt.get("sort_cost", "Koszt"):
            filtered_subs.sort(key=lambda x: float(x.get("cost", 0.0)), reverse=True)
        elif sort_val == self.txt.get("sort_expiry", "Data wygaśnięcia"):
            filtered_subs.sort(key=lambda x: x.get("expiry_date") or "9999-99-99")
        else:  # Domyślnie sortuj po dacie płatności
            filtered_subs.sort(key=lambda x: x.get("billing_date") or "9999-99-99")

        # Rysowanie tabeli
        count = 0
        for sub in filtered_subs:
            is_active = sub.get("is_active", True)
            tag = "active_normal"
            icon = "●" if is_active else "○"

            # --- Obliczanie Dni do Płatności ---
            b_date_str = sub.get("billing_date") or ""
            e_date_str = sub.get("expiry_date") or ""
            b_days_str = "-"
            b_display_date = "-"

            if b_date_str:
                # Jeśli data płatności to dzień wygaśnięcia -> nie ma kolejnej płatności
                if b_date_str == e_date_str and e_date_str != "":
                    b_days_str = "—"
                    b_display_date = "—"
                else:
                    try:
                        b_date = datetime.strptime(b_date_str, "%Y-%m-%d").date()
                        days = (b_date - today).days
                        b_days_str = f"{days} dni" if days > 0 else self.txt.get("tag_today",
                                                                                 "Dzisiaj!") if days == 0 else "!"
                        b_display_date = b_date_str
                    except:
                        pass

            # --- Obliczanie Dni do Wygaśnięcia ---
            e_date_str = sub.get("expiry_date", "") or ""
            e_days_str = "∞"
            e_display_date = "∞"

            if not is_active:
                tag = "inactive"
                b_days_str = self.txt.get("sub_status_inactive", "Nieaktywna")
                e_days_str = "-"
            elif e_date_str:
                try:
                    e_date = datetime.strptime(e_date_str, "%Y-%m-%d").date()
                    days = (e_date - today).days
                    e_days_str = f"{days} dni"
                    e_display_date = e_date_str

                    if days < 0:
                        e_days_str = self.txt.get("sub_expired", "Wygasła!")
                        tag = "active_danger"
                    elif days <= 7:
                        tag = "active_danger"
                    elif days <= 30:
                        tag = "active_warning"
                except:
                    pass

            cost_str = f"{sub.get('cost', 0.0)} {sub.get('currency', 'PLN')}"

            # Zapisz stany do pamięci, aby zmieniać je przy selekcji
            self.row_display_data[sub["id"]] = {
                "b_date": b_display_date,
                "b_days": b_days_str,
                "e_date": e_display_date,
                "e_days": e_days_str
            }

            self.tree.insert("", "end", iid=sub["id"],
                             values=(icon, sub["name"], sub.get("provider", ""), cost_str, b_days_str, e_days_str),
                             tags=(tag,))
            count += 1

        if count == 0:
            self.lbl_empty.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_empty.lift()
        else:
            self.lbl_empty.place_forget()

    def on_select(self, event):
        """Podmienia tekst (ilość dni <-> konkretna data) po kliknięciu elementu."""
        selected = self.tree.selection()

        for item_id in self.tree.get_children():
            data = self.row_display_data.get(item_id)
            if not data: continue

            # Pobieramy obecne wartości, żeby nie zepsuć kolumn ze stałym tekstem (Nazwa, Koszt itd.)
            vals = list(self.tree.item(item_id, "values"))

            if item_id in selected:
                vals[4] = data["b_date"]  # Pokazuj dokładną datę
                vals[5] = data["e_date"]
            else:
                vals[4] = data["b_days"]  # Pokaż ilość dni
                vals[5] = data["e_days"]

            self.tree.item(item_id, values=vals)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def on_double_click(self, event):
        self.edit_selected()

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected: return
        sub_id = selected[0]

        sub_data = self.storage.get_subscription(sub_id)
        if sub_data and self.drawer:
            from gui.dialogs.subscription_panel import ManageSubscriptionPanel
            self.drawer.set_content(ManageSubscriptionPanel, txt=self.txt, btn_style=self.btn_style,
                                    storage=self.storage, refresh_callback=self.refresh_table,
                                    close_callback=self.drawer.close_panel, sub_data=sub_data)

    def open_add_panel(self):
        if self.drawer:
            from gui.dialogs.subscription_panel import ManageSubscriptionPanel
            self.drawer.set_content(ManageSubscriptionPanel, txt=self.txt, btn_style=self.btn_style,
                                    storage=self.storage, refresh_callback=self.refresh_table,
                                    close_callback=self.drawer.close_panel)

    def toggle_active(self):
        selected = self.tree.selection()
        if not selected: return
        sub_id = selected[0]

        sub_data = self.storage.get_subscription(sub_id)
        if sub_data:
            sub_data["is_active"] = not sub_data.get("is_active", True)
            self.storage.update_subscription(sub_data)
            self.refresh_table()

    def delete_selected(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        sub_id = selected[0]

        if messagebox.askyesno(self.txt.get("btn_delete", "Usuń"),
                               self.txt.get("msg_confirm_delete", "Czy na pewno chcesz to usunąć?")):
            self.storage.delete_subscription(sub_id)
            self.refresh_table()