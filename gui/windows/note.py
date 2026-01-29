import customtkinter as ctk
from core.storage import save


class NoteWindow:
    def __init__(self, parent, txt, data, btn_style, topic_data):
        self.data = data
        self.topic_data = topic_data

        # Tworzymy okno
        self.win = ctk.CTkToplevel(parent)
        self.win.title(txt.get("win_note_title", "Notatki"))
        self.win.geometry("400x350")

        # Tytuł tematu na górze (dla kontekstu)
        ctk.CTkLabel(self.win, text=topic_data["name"], font=("Arial", 14, "bold"), wraplength=380).pack(pady=(10, 5))

        # Pole tekstowe
        self.text_area = ctk.CTkTextbox(self.win, width=380, height=200, font=("Arial", 12))
        self.text_area.pack(padx=10, pady=5, fill="both", expand=True)

        # Wczytanie istniejącej notatki (jeśli jest)
        current_note = topic_data.get("note", "")
        self.text_area.insert("0.0", current_note)

        # Przycisk Zapisz
        ctk.CTkButton(self.win, text=txt.get("btn_save", "Zapisz"), command=self.save_note, **btn_style).pack(pady=10)

    def save_note(self):
        # Pobieramy tekst (od początku "0.0" do końca "end-1c", żeby uciąć ostatni znak nowej linii)
        content = self.text_area.get("0.0", "end-1c")

        # Zapisujemy w strukturze tematu
        self.topic_data["note"] = content
        save(self.data)

        self.win.destroy()