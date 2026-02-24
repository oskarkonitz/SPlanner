import customtkinter as ctk
import tkinter as tk
import uuid
from tkcalendar import DateEntry


class ManageSubscriptionPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, refresh_callback, close_callback, sub_data=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.refresh_callback = refresh_callback
        self.close_callback = close_callback
        self.sub_data = sub_data

        title_key = "btn_edit_sub" if sub_data else "btn_add_sub"
        ctk.CTkLabel(self, text=self.txt.get(title_key, "Subscription"), font=("Arial", 20, "bold")).pack(pady=(20, 15))

        # Nazwa i Dostawca
        ctk.CTkLabel(self, text=self.txt.get("sub_name", "Name"), anchor="w").pack(fill="x", padx=20)
        self.e_name = ctk.CTkEntry(self)
        self.e_name.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(self, text=self.txt.get("sub_provider", "Provider"), anchor="w").pack(fill="x", padx=20)
        self.e_provider = ctk.CTkEntry(self)
        self.e_provider.pack(fill="x", padx=20, pady=(0, 10))

        # Cena i Waluta
        ctk.CTkLabel(self, text=self.txt.get("sub_cost", "Cost & Currency"), anchor="w").pack(fill="x", padx=20)
        cost_frame = ctk.CTkFrame(self, fg_color="transparent")
        cost_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.e_cost = ctk.CTkEntry(cost_frame, width=100)
        self.e_cost.pack(side="left", padx=(0, 10))

        self.cb_currency = ctk.CTkComboBox(cost_frame, values=["PLN", "USD", "EUR", "GBP"], width=80)
        self.cb_currency.pack(side="left")

        # Cykl Rozliczeniowy
        ctk.CTkLabel(self, text=self.txt.get("sub_cycle", "Billing Cycle"), anchor="w").pack(fill="x", padx=20)
        cycle_opts = [
            self.txt.get("cycle_monthly", "Monthly"),
            self.txt.get("cycle_yearly", "Yearly"),
            self.txt.get("cycle_one_time", "One-time")
        ]
        self.cb_cycle = ctk.CTkComboBox(self, values=cycle_opts)
        self.cb_cycle.pack(fill="x", padx=20, pady=(0, 10))

        # Data Rozliczenia (Billing Date)
        ctk.CTkLabel(self, text=self.txt.get("sub_billing_date", "Billing Date"), anchor="w").pack(fill="x", padx=20)
        self.cal_billing = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2,
                                     date_pattern='yyyy-mm-dd')
        self.cal_billing.pack(fill="x", padx=20, pady=(0, 10))

        # Data wygaśnięcia z Checkboxem
        exp_top_frame = ctk.CTkFrame(self, fg_color="transparent")
        exp_top_frame.pack(fill="x", padx=15, pady=(5, 0))

        self.has_expiry_var = tk.BooleanVar(value=True)
        self.chk_expiry = ctk.CTkCheckBox(exp_top_frame, text=self.txt.get("sub_has_expiry", "Has expiry date?"),
                                          variable=self.has_expiry_var, command=self.toggle_expiry)
        self.chk_expiry.pack(side="left", pady=5)

        self.cal_expiry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2,
                                    date_pattern='yyyy-mm-dd')
        self.cal_expiry.pack(fill="x", padx=20, pady=(0, 20))

        # Wypełnianie danymi
        if self.sub_data:
            self.e_name.insert(0, self.sub_data.get("name", ""))
            self.e_provider.insert(0, self.sub_data.get("provider", ""))
            self.e_cost.insert(0, str(self.sub_data.get("cost", 0.0)))
            self.cb_currency.set(self.sub_data.get("currency", "PLN"))

            if self.sub_data.get("billing_date"):
                self.cal_billing.set_date(self.sub_data["billing_date"])

            if self.sub_data.get("expiry_date"):
                self.has_expiry_var.set(True)
                self.cal_expiry.set_date(self.sub_data["expiry_date"])
                self.cal_expiry.configure(state="normal")
            else:
                self.has_expiry_var.set(False)
                self.cal_expiry.configure(state="disabled")

        # Przyciski ze stylem
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(
            btn_frame,
            text=self.txt.get("btn_save", "Save"),
            command=self.save,
            **self.btn_style
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            btn_frame,
            text=self.txt.get("btn_cancel", "Cancel"),
            command=self.close_callback,
            fg_color="transparent",
            border_width=1.2,
            border_color=self.btn_style.get("border_color", "gray"),
            text_color=("gray10", "gray90"),
            hover_color=self.btn_style.get("hover_color", "#454545")
        ).pack(side="right", padx=5)

    def toggle_expiry(self):
        if self.has_expiry_var.get():
            self.cal_expiry.configure(state="normal")
        else:
            self.cal_expiry.configure(state="disabled")

    def save(self):
        name = self.e_name.get().strip()
        if not name: return

        try:
            cost_val = float(self.e_cost.get().strip().replace(',', '.'))
        except ValueError:
            cost_val = 0.0

        exp_date = self.cal_expiry.get() if self.has_expiry_var.get() else ""

        data = {
            "id": self.sub_data["id"] if self.sub_data else str(uuid.uuid4()),
            "name": name,
            "provider": self.e_provider.get().strip(),
            "cost": cost_val,
            "currency": self.cb_currency.get(),
            "billing_date": self.cal_billing.get(),
            "expiry_date": exp_date,
            "billing_cycle": self.cb_cycle.get(),
            "is_active": self.sub_data.get("is_active", True) if self.sub_data else True
        }

        if self.sub_data:
            self.storage.update_subscription(data)
        else:
            self.storage.add_subscription(data)

        if self.refresh_callback:
            self.refresh_callback()
        self.close_callback()