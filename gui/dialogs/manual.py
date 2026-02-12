import tkinter as tk
import customtkinter as ctk


class ManualWindow:
    def __init__(self, parent, txt, btn_style):
        # ustawienie okna
        self.win = ctk.CTkToplevel(parent)
        self.win.title(txt["manual_title"])
        self.win.geometry("600x500")

        # --- ZMIANA 1: Używamy ctk.CTkFrame zamiast tk.Frame ---
        # fg_color="transparent" sprawia, że ramka jest niewidoczna i przyjmuje kolor okna
        frame = ctk.CTkFrame(self.win, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # --- ZMIANA 2: Definicja pola tekstowego (musimy je stworzyć przed podpięciem do scrolla) ---
        # Używamy standardowego tk.Text, bo obsługuje tagi (bold), ale usuwamy obramowanie (bd=0)
        text = tk.Text(frame, wrap="word", padx=10, pady=10, bd=0, highlightthickness=0)

        # --- ZMIANA 3: Nowy scrollbar CustomTkinter ---
        scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=text.yview, fg_color="transparent", bg_color="transparent")

        # Podpięcie scrolla do tekstu
        text.configure(yscrollcommand=scrollbar.set)

        # --- ZMIANA 4: Pakowanie (Scrollbar po prawej, tekst po lewej) ---
        scrollbar.pack(side="right", fill="y", padx=(0, 5))  # padx żeby lekko odsunąć od krawędzi
        text.pack(side="left", fill="both", expand=True)

        # formatowanie tekstu
        text.tag_config("bold", font=("Arial", 20, "bold"))
        text.tag_config("normal", font=("Arial", 13))

        # wstawienie tekstu instrukcji z pliku jezykowego
        text.insert("end", txt["manual_header"], "bold")
        text.insert("end", "\n\n")  # dodajemy odstęp po nagłówku
        text.insert("end", txt["manual_content"], "normal")
        text.configure(state="disabled")  # zablokowanie edycji

        # przycisk zamykania
        btn_close = ctk.CTkButton(self.win, text=txt["btn_close"], command=self.win.destroy, **btn_style)
        btn_close.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
        btn_close.pack(side="bottom", pady=10)