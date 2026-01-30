import customtkinter as ctk
from core.storage import save


class NoteWindow:
    def __init__(self, parent, txt, data, btn_style, item_data):
        self.data = data
        self.item_data = item_data

        # ... (reszta init bez zmian) ...
        # Tworzymy okno
        self.win = ctk.CTkToplevel(parent)
        self.win.title(txt.get("win_note_title", "Notatki"))
        self.win.geometry("400x350")

        # --- POPRAWKA: Rozpoznawanie nazwy (Temat vs Egzamin) ---
        if "name" in item_data:
            display_title = item_data["name"]
        else:
            subj = item_data.get("subject", "???")
            title = item_data.get("title", "???")
            display_title = f"{subj} ({title})"
        # --------------------------------------------------------

        ctk.CTkLabel(self.win, text=display_title, font=("Arial", 14, "bold"), wraplength=380).pack(pady=(10, 5))

        self.text_area = ctk.CTkTextbox(self.win, width=380, height=200, font=("Arial", 12))
        self.text_area.pack(padx=10, pady=5, fill="both", expand=True)

        current_note = item_data.get("note", "")
        self.text_area.insert("0.0", current_note)

        ctk.CTkButton(self.win, text=txt.get("btn_save", "Zapisz"), command=self.save_note, **btn_style).pack(pady=10)

    def save_note(self):
        content = self.text_area.get("0.0", "end-1c")

        # Sprawdzamy, czy dodano nową treść do pustej notatki (dla osiągnięcia Scribe)
        old_content = self.item_data.get("note", "").strip()
        new_content_stripped = content.strip()

        if not old_content and new_content_stripped:
            if "global_stats" not in self.data: self.data["global_stats"] = {}
            curr = self.data["global_stats"].get("notes_added", 0)
            self.data["global_stats"]["notes_added"] = curr + 1

        self.item_data["note"] = content
        save(self.data)

        self.win.destroy()