import customtkinter as ctk
import tkinter as tk
from core.storage import save


class NotebookWindow:
    def __init__(self, parent, txt, data, btn_style, exam_data):
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.exam_data = exam_data

        self.topics = [t for t in self.data["topics"] if t["exam_id"] == exam_data["id"]]
        self.topics.sort(key=lambda x: str(x.get("scheduled_date") or "9999-99-99"))

        self.current_item = None
        self.buttons_map = {}

        # USTAWIENIE OKNA
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_notebook_title", "Notatnik Egzaminu"))
        self.win.geometry("800x500")

        self.win.columnconfigure(1, weight=1)
        self.win.rowconfigure(0, weight=1)

        # --- LEWY PANEL (MENU) ---
        self.left_frame = ctk.CTkScrollableFrame(self.win, width=250, corner_radius=0)
        self.left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)

        ctk.CTkLabel(self.left_frame, text=self.txt.get("notebook_list_header", "Lista elementów"),
                     font=("Arial", 12, "bold"), text_color="gray").pack(pady=5, anchor="w", padx=10)

        # --- PRAWY PANEL (EDYTOR) ---
        self.right_frame = ctk.CTkFrame(self.win, corner_radius=0, fg_color="transparent")
        self.right_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.lbl_current_title = ctk.CTkLabel(self.right_frame, text="", font=("Arial", 16, "bold"), anchor="w")
        self.lbl_current_title.pack(fill="x", padx=20, pady=(15, 5))

        self.text_area = ctk.CTkTextbox(self.right_frame, font=("Arial", 13), wrap="word")
        self.text_area.pack(fill="both", expand=True, padx=20, pady=5)

        btn_close = ctk.CTkButton(self.right_frame, text=self.txt["btn_close"], command=self.on_close,
                                  fg_color="transparent", border_width=1, border_color="gray",
                                  text_color=("gray10", "gray90"))
        btn_close.pack(side="bottom", anchor="e", padx=20, pady=20)

        self.populate_list()
        self.load_item(self.exam_data, btn_id="exam")

    def populate_list(self):
        # 1. Przycisk Egzaminu (Główny)
        # Usunąłem emotkę folderu, zostawiłem czysty tekst
        btn_exam = ctk.CTkButton(self.left_frame,
                                 text=self.txt.get('notebook_exam_general', 'Ogólne (Egzamin)'),
                                 fg_color="transparent", text_color=("gray10", "gray90"), anchor="w",
                                 hover_color=("gray85", "gray25"),
                                 command=lambda: self.switch_to(self.exam_data, "exam"))
        btn_exam.pack(fill="x", pady=2)
        self.buttons_map["exam"] = btn_exam

        # Separator
        tk.Frame(self.left_frame, height=1, bg="gray").pack(fill="x", pady=5, padx=10)

        # 2. Lista Tematów
        for i, topic in enumerate(self.topics):
            # --- ZMIANA IKON ---
            has_note = bool(topic.get("note", "").strip())
            # Używamy ołówka ✎ zamiast emotki, i spacji jeśli brak notatki (bez ikonki kartki)
            prefix = "✎ " if has_note else "   "

            # Skrócona nazwa
            name = topic["name"]
            if len(name) > 30: name = name[:27] + "..."

            btn_id = f"topic_{topic['id']}"
            btn = ctk.CTkButton(self.left_frame,
                                text=f"{prefix}{name}",
                                fg_color="transparent", text_color=("gray10", "gray90"), anchor="w",
                                hover_color=("gray85", "gray25"),
                                command=lambda t=topic, bid=btn_id: self.switch_to(t, bid))
            btn.pack(fill="x", pady=1)
            self.buttons_map[btn_id] = btn

    def switch_to(self, new_item, new_btn_id):
        self.save_current_note()
        self.load_item(new_item, new_btn_id)

    def load_item(self, item, btn_id):
        self.current_item = item

        for bid, btn in self.buttons_map.items():
            if bid == btn_id:
                btn.configure(fg_color=("gray80", "gray30"))
            else:
                btn.configure(fg_color="transparent")

        if item == self.exam_data:
            title = f"{item['subject']} - {self.txt.get('notebook_exam_general', 'Notatki ogólne')}"
        else:
            title = item["name"]

        self.lbl_current_title.configure(text=title)

        content = item.get("note", "")
        self.text_area.delete("0.0", "end")
        self.text_area.insert("0.0", content)

    def save_current_note(self):
        if self.current_item is not None:
            new_text = self.text_area.get("0.0", "end-1c")
            self.current_item["note"] = new_text
            save(self.data)

    def on_close(self):
        self.save_current_note()
        self.win.destroy()