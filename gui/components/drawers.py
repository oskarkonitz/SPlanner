import customtkinter as ctk

# --- KLASA PANELU BOCZNEGO (DRAWER) ---
class NoteDrawer(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, save_callback):
        super().__init__(parent, corner_radius=0, fg_color=("gray90", "gray20"))
        self.txt = txt
        self.save_callback = save_callback
        self.current_item_data = None
        self.is_open = False

        # ID procesu animacji
        self.animation_id = None

        # Pozycja startowa (poza ekranem z prawej strony)
        self.target_x = 1.05
        self.place(relx=self.target_x, rely=0, relwidth=0.3, relheight=1.0)

        # --- UI PANELU ---
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=10, pady=10)

        title_text = self.txt.get("drawer_title", "Notatka")
        self.lbl_title = ctk.CTkLabel(self.header_frame, text=title_text, font=("Arial", 16, "bold"), anchor="w")
        self.lbl_title.pack(side="left", fill="x", expand=True)

        self.btn_close = ctk.CTkButton(self.header_frame, text="✕", width=30, height=30,
                                       fg_color="transparent", text_color="gray", hover_color=("gray80", "gray30"),
                                       command=self.close_panel)
        self.btn_close.pack(side="right")

        self.lbl_item_name = ctk.CTkLabel(self, text="...", font=("Arial", 12), text_color="gray",
                                          anchor="w", wraplength=200)
        self.lbl_item_name.pack(fill="x", padx=15, pady=(0, 10))

        self.textbox = ctk.CTkTextbox(self, font=("Arial", 13), wrap="word")
        self.textbox.pack(fill="both", expand=True, padx=10, pady=5)

        self.btn_save = ctk.CTkButton(self, text=self.txt.get("btn_save", "Zapisz"), command=self.save_note,
                                      **btn_style)
        self.btn_save.pack(pady=15, padx=10, fill="x")

    def load_note(self, item_data, item_name):
        self.stop_animation()

        # item_data jest słownikiem (kopią z DB), który edytujemy lokalnie w drawerze
        self.current_item_data = item_data
        self.lbl_item_name.configure(text=item_name)
        note_content = item_data.get("note", "")

        # Czyścimy i wstawiamy (nawet jeśli puste)
        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", note_content)

        # Zapobieganie "glitchowi" wizualnemu przy ponownym otwieraniu
        try:
            current_x = float(self.place_info().get('relx', self.target_x))
            if current_x > 1.0:
                self.place(relx=1.0)  # Ustaw na krawędzi przed wjazdem
        except:
            pass

        self.open_panel()

    def save_note(self):
        if self.current_item_data is not None:
            new_text = self.textbox.get("0.0", "end-1c")
            old_text = self.current_item_data.get("note", "").strip()

            is_new = (not old_text and new_text.strip() != "")

            self.current_item_data["note"] = new_text
            self.save_callback(is_new_note=is_new)

            saved_txt = self.txt.get("btn_saved", "Zapisano!")
            orig_text = self.txt.get("btn_save", "Zapisz")
            self.btn_save.configure(text=saved_txt, fg_color="#27ae60")
            self.after(1500, lambda: self.btn_save.configure(text=orig_text, fg_color="#3a3a3a"))

    def stop_animation(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None

    def open_panel(self):
        self.stop_animation()
        self.is_open = True
        self.tkraise()
        self.lift()
        self.animate(0.7)

    def close_panel(self):
        self.stop_animation()
        self.is_open = False
        self.animate(1.05)

    def animate(self, target):
        try:
            current_val = self.place_info().get('relx')
        except (TypeError, KeyError, AttributeError):
            return

        if current_val is None:
            current = self.target_x
        else:
            current = float(current_val)

        if abs(target - current) < 0.005:
            self.place(relx=target)
            self.animation_id = None
            return

        diff = target - current
        step = diff * 0.25
        if abs(step) < 0.001: step = 0.001 if diff > 0 else -0.001

        self.place(relx=current + step)
        self.animation_id = self.after(16, lambda: self.animate(target))


# --- KLASA: LEWA SZUFLADKA (Z BEZPIECZNIKIEM KLIKNIĘĆ) ---
class ToolsDrawer(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, callbacks):
        super().__init__(parent, width=220, corner_radius=20, fg_color=("gray90", "gray20"))

        self.txt = txt
        self.callbacks = callbacks
        self.is_open = False
        self.animation_id = None
        self.ignore_click = False

        # Pozycja ukryta
        self.target_x = 0.01
        self.hidden_x = -0.3

        self.place(relx=self.hidden_x, rely=0.15)

        # UI - Nagłówek
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(head, text=self.txt.get("drawer_tools_title", "Tools"),
                     font=("Arial", 14, "bold")).pack(side="left")

        ctk.CTkButton(head, text="✕", width=25, height=25, fg_color="transparent",
                      text_color="gray", hover_color=("gray85", "gray30"),
                      command=self.close_panel).pack(side="right")

        # Kontener na przyciski
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Helper do przycisków
        def add_btn(text_key, cmd, color=None):
            current_hover = btn_style.get("hover_color", "#454545")

            if color:
                # STYL OUTLINE
                btn = ctk.CTkButton(content_frame,
                                    text=self.txt.get(text_key, text_key),
                                    command=lambda: [cmd(), self.close_panel()],
                                    height=35,
                                    corner_radius=17,
                                    fg_color="transparent",
                                    border_color=color,
                                    text_color=color,
                                    border_width=1.2,
                                    hover_color=current_hover)
            else:
                # STYL SOLID
                current_text_col = btn_style.get("text_color", "white")
                btn = ctk.CTkButton(content_frame,
                                    text=self.txt.get(text_key, text_key),
                                    command=lambda: [cmd(), self.close_panel()],
                                    height=35,
                                    corner_radius=17,
                                    fg_color=btn_style["fg_color"],
                                    text_color=current_text_col,
                                    border_color=btn_style.get("border_color", "gray"),
                                    border_width=1,
                                    hover_color=current_hover)

            btn.pack(fill="x", pady=4)

        add_btn("menu_timer", self.callbacks["timer"], "#e6b800")
        add_btn("win_achievements", self.callbacks["achievements"], "violet")
        add_btn("menu_days_off", self.callbacks["days_off"], "#5dade2")
        add_btn("menu_subjects", self.callbacks["subjects"], "#e67e22")
        add_btn("menu_grades", self.callbacks["grades"], "#9b59b6")

        ctk.CTkFrame(content_frame, height=2, fg_color="gray80").pack(fill="x", pady=10)

        add_btn("btn_gen_full", self.callbacks["gen_full"])
        add_btn("btn_gen_new", self.callbacks["gen_new"])

        # --- CLICK OUTSIDE LOGIC ---
        self.bind_id = self.winfo_toplevel().bind("<Button-1>", self.check_click_outside, add="+")

    def check_click_outside(self, event):
        # Jeśli zamknięta LUB flaga ignorowania jest aktywna -> nie rób nic
        if not self.is_open or self.ignore_click:
            return

        try:
            x = self.winfo_rootx()
            y = self.winfo_rooty()
            w = self.winfo_width()
            h = self.winfo_height()
        except:
            return

            # Jeśli kliknięcie wewnątrz szufladki -> nie zamykaj
        if x <= event.x_root <= x + w and y <= event.y_root <= y + h:
            return

            # Kliknięcie na zewnątrz -> zamykamy
        self.close_panel()

    def open_panel(self):
        self.lift()
        self.is_open = True

        # Blokujemy zamykanie na 150ms po otwarciu
        self.ignore_click = True
        self.after(150, lambda: setattr(self, 'ignore_click', False))

        self.animate(self.target_x)

    def close_panel(self):
        self.is_open = False
        self.animate(self.hidden_x)

    def animate(self, target):
        try:
            current = float(self.place_info().get('relx'))
        except:
            return

        if abs(target - current) < 0.005:
            self.place(relx=target)
            return

        step = (target - current) * 0.25
        self.place(relx=current + step)
        self.after(16, lambda: self.animate(target))