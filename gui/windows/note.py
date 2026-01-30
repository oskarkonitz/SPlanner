import customtkinter as ctk
from core.storage import save


class NoteWindow:
    def __init__(self, parent, txt, data, btn_style, item_data):
        self.data = data
        self.item_data = item_data

        # Tworzymy okno
        self.win = ctk.CTkToplevel(parent)
        self.win.title(txt.get("win_note_title", "Notatki"))
        self.win.geometry("400x350")

        # --- POPRAWKA: Rozpoznawanie nazwy (Temat vs Egzamin) ---
        # Temat ma klucz "name", a Egzamin ma "subject" i "title"
        if "name" in item_data:
            display_title = item_data["name"]
        else:
            # Formatowanie dla egzaminu: "Matematyka (Kolokwium)"
            subj = item_data.get("subject", "???")
            title = item_data.get("title", "???")
            display_title = f"{subj} ({title})"
        # --------------------------------------------------------

        # Tytuł elementu na górze (dla kontekstu)
        ctk.CTkLabel(self.win, text=display_title, font=("Arial", 14, "bold"), wraplength=380).pack(pady=(10, 5))

        # Pole tekstowe
        self.text_area = ctk.CTkTextbox(self.win, width=380, height=200, font=("Arial", 12))
        self.text_area.pack(padx=10, pady=5, fill="both", expand=True)

        # Wczytanie istniejącej notatki (jeśli jest)
        current_note = item_data.get("note", "")
        self.text_area.insert("0.0", current_note)

        # Przycisk Zapisz
        ctk.CTkButton(self.win, text=txt.get("btn_save", "Zapisz"), command=self.save_note, **btn_style).pack(pady=10)

    def save_note(self):
        # Pobieramy tekst (od początku "0.0" do końca "end-1c", żeby uciąć ostatni znak nowej linii)
        content = self.text_area.get("0.0", "end-1c")

        # Zapisujemy w strukturze przekazanego obiektu (tematu lub egzaminu)
        self.item_data["note"] = content
        save(self.data)

        self.win.destroy()