import customtkinter as ctk
from tkinter import messagebox
import threading
import time


class LoginWindow(ctk.CTkToplevel):
    def __init__(self, parent, txt, storage, on_success_callback):
        super().__init__(parent)
        self.txt = txt
        self.storage = storage
        self.on_success_callback = on_success_callback
        self.is_login_mode = True

        self.title(self.txt.get("win_login_title", "StudyPlanner - Autoryzacja"))
        self.geometry("400x480")
        self.resizable(False, False)

        # Wymuszamy, by okno autoryzacji było na wierzchu (przydatne przy splash screenie)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._center_window(400, 480)
        self.setup_ui()

    def _center_window(self, width, height):
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def setup_ui(self):
        # Główny kontener
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=40, pady=40)

        # Tytuł
        self.lbl_title = ctk.CTkLabel(
            self.main_frame,
            text=self.txt.get("lbl_login_title", "Witaj ponownie!"),
            font=("Arial", 24, "bold")
        )
        self.lbl_title.pack(pady=(0, 30))

        # Pole Email
        self.entry_email = ctk.CTkEntry(
            self.main_frame,
            placeholder_text=self.txt.get("ph_email", "Adres e-mail"),
            width=300,
            height=40,
            font=("Arial", 14)
        )
        self.entry_email.pack(pady=(0, 15))

        # Pole Hasło
        self.entry_pwd = ctk.CTkEntry(
            self.main_frame,
            placeholder_text=self.txt.get("ph_password", "Hasło"),
            show="*",
            width=300,
            height=40,
            font=("Arial", 14)
        )
        self.entry_pwd.pack(pady=(0, 10))

        # Komunikat o statusie/błędzie (domyślnie ukryty)
        self.lbl_error = ctk.CTkLabel(
            self.main_frame,
            text="",
            text_color="#e74c3c",
            font=("Arial", 12),
            wraplength=280
        )
        self.lbl_error.pack(pady=(0, 10))

        # Główny przycisk akcji
        self.btn_submit = ctk.CTkButton(
            self.main_frame,
            text=self.txt.get("btn_login", "Zaloguj się"),
            font=("Arial", 14, "bold"),
            width=300,
            height=40,
            corner_radius=20,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self.submit
        )
        self.btn_submit.pack(pady=(10, 20))

        # Przełącznik trybu (Logowanie <-> Rejestracja)
        self.btn_toggle_mode = ctk.CTkButton(
            self.main_frame,
            text=self.txt.get("lbl_no_account", "Nie masz konta? Zarejestruj się"),
            fg_color="transparent",
            text_color="gray",
            hover_color="#2b2b2b",
            font=("Arial", 12, "underline"),
            command=self.toggle_mode
        )
        self.btn_toggle_mode.pack(side="bottom")

    def toggle_mode(self):
        self.is_login_mode = not self.is_login_mode
        self.lbl_error.configure(text="")  # Czyścimy błędy przy zmianie trybu

        if self.is_login_mode:
            self.lbl_title.configure(text=self.txt.get("lbl_login_title", "Witaj ponownie!"))
            self.btn_submit.configure(text=self.txt.get("btn_login", "Zaloguj się"))
            self.btn_toggle_mode.configure(text=self.txt.get("lbl_no_account", "Nie masz konta? Zarejestruj się"))
        else:
            self.lbl_title.configure(text=self.txt.get("lbl_register_title", "Stwórz konto"))
            self.btn_submit.configure(text=self.txt.get("btn_register", "Zarejestruj się"))
            self.btn_toggle_mode.configure(text=self.txt.get("lbl_has_account", "Masz już konto? Zaloguj się"))

    def show_message(self, text, color="#e74c3c"):
        self.lbl_error.configure(text=text, text_color=color)

    def submit(self):
        email = self.entry_email.get().strip()
        password = self.entry_pwd.get().strip()

        if not email or not password:
            self.show_message(self.txt.get("err_empty_fields", "Wypełnij wszystkie pola."))
            return

        if not self.is_login_mode and len(password) < 6:
            self.show_message(self.txt.get("err_pwd_short", "Hasło musi mieć min. 6 znaków."))
            return

        # Zablokuj okno, aby uniknąć wielokrotnych kliknięć
        self.btn_submit.configure(state="disabled")
        self.entry_email.configure(state="disabled")
        self.entry_pwd.configure(state="disabled")

        self.show_message(self.txt.get("msg_processing", "Przetwarzanie..."), color="gray")

        # Odpalamy zapytanie w tle, żeby nie zablokować UI
        threading.Thread(target=self._auth_worker, args=(email, password), daemon=True).start()

    def _auth_worker(self, email, password):
        try:
            if self.is_login_mode:
                user = self.storage.login(email, password)
            else:
                user = self.storage.register(email, password)

            if user:
                # KROK 5: Ustawienie trybu na chmurę dla aplikacji
                self.storage.config["db_mode"] = "cloud"
                self.storage.mode = "cloud"
                self.storage.mark_onboarding_done()

                # Synchronizacja danych po udanym logowaniu
                def sync_status_update(msg):
                    self.after(0, lambda m=msg: self.show_message(m, color="#3498db"))

                self.storage.sync_down(status_callback=sync_status_update)

                # Dajemy użytkownikowi moment na przeczytanie komunikatu "Ready!"
                self.after(0, lambda: self.show_message(self.txt.get("msg_sync_done", "Gotowe! Uruchamianie..."),
                                                        color="#2ecc71"))
                time.sleep(0.5)

                # Sukces -> wracamy do głównego wątku UI i odpalamy callback
                self.after(0, self.on_success)
            else:
                self.after(0, lambda: self.show_message(self.txt.get("err_auth_failed", "Błąd autoryzacji.")))
                self.after(0, self._unlock_ui)

        except Exception as e:
            error_msg = str(e)

            # Tłumaczenie typowych błędów Supabase na przyjaźniejsze komunikaty
            if "Invalid login credentials" in error_msg:
                error_msg = self.txt.get("err_invalid_creds", "Nieprawidłowy e-mail lub hasło.")
            elif "User already registered" in error_msg:
                error_msg = self.txt.get("err_user_exists", "Konto z tym adresem e-mail już istnieje.")

            self.after(0, lambda e=error_msg: self.show_message(e))
            self.after(0, self._unlock_ui)

    def _unlock_ui(self):
        self.btn_submit.configure(state="normal")
        self.entry_email.configure(state="normal")
        self.entry_pwd.configure(state="normal")

    def on_success(self):
        self.destroy()
        self.on_success_callback()

    def on_close(self):
        # Jeśli użytkownik zamknie okno logowania krzyżykiem, zamykamy całą aplikację
        self.destroy()
        self.master.quit()