import customtkinter as ctk


# --- KLASA PANELU BOCZNEGO (NOTATKI - LEGACY) ---
class NoteDrawer(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, save_callback):
        super().__init__(parent, corner_radius=20, border_width=1 , border_color=("black", "white"), fg_color=("gray90", "gray20"))
        self.txt = txt
        self.save_callback = save_callback
        self.current_item_data = None
        self.is_open = False
        self.animation_id = None

        # Pozycja startowa (poza ekranem z prawej strony)
        self.target_x = 1.05
        self.place(relx=self.target_x, rely=0.02, relwidth=0.3, relheight=0.96)

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
        self.current_item_data = item_data
        self.lbl_item_name.configure(text=item_name)
        note_content = item_data.get("note") or ""

        self.textbox.delete("0.0", "end")
        self.textbox.insert("0.0", note_content)

        try:
            current_x = float(self.place_info().get('relx', self.target_x))
            if current_x > 1.0:
                self.place(relx=1.0)
        except:
            pass
        self.open_panel()

    def save_note(self):
        if self.current_item_data is not None:
            new_text = self.textbox.get("0.0", "end-1c")
            old_text = (self.current_item_data.get("note") or "").strip()
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
        self.animate(0.69)

    def close_panel(self):
        self.stop_animation()
        self.is_open = False
        self.animate(1.05)

    def animate(self, target):
        try:
            current_val = self.place_info().get('relx')
        except:
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


# --- KLASA: LEWA SZUFLADKA ---
class ToolsDrawer(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, callbacks):
        super().__init__(parent, width=220, corner_radius=20, border_width=1 , border_color=("black", "white"), fg_color=("gray90", "gray20"))
        self.txt = txt
        self.callbacks = callbacks
        self.is_open = False
        self.animation_id = None
        self.ignore_click = False
        self.target_x = 0.01
        self.hidden_x = -0.3

        self.place(relx=self.hidden_x, rely=0.15)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(head, text=self.txt.get("drawer_tools_title", "Tools"), font=("Arial", 14, "bold")).pack(
            side="left")
        ctk.CTkButton(head, text="✕", width=25, height=25, fg_color="transparent",
                      text_color="gray", hover_color=("gray85", "gray30"),
                      command=self.close_panel).pack(side="right")

        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def add_btn(text_key, cmd, color=None):
            current_hover = btn_style.get("hover_color", "#454545")
            if color:
                btn = ctk.CTkButton(content_frame, text=self.txt.get(text_key, text_key),
                                    command=lambda: [cmd(), self.close_panel()], height=35, corner_radius=17,
                                    fg_color="transparent", border_color=color, text_color=color, border_width=1.2,
                                    hover_color=current_hover)
            else:
                current_text_col = btn_style.get("text_color", "white")
                btn = ctk.CTkButton(content_frame, text=self.txt.get(text_key, text_key),
                                    command=lambda: [cmd(), self.close_panel()], height=35, corner_radius=17,
                                    fg_color=btn_style["fg_color"], text_color=current_text_col,
                                    border_color=btn_style.get("border_color", "gray"), border_width=1,
                                    hover_color=current_hover)
            btn.pack(fill="x", pady=4)

        add_btn("menu_timer", self.callbacks["timer"], "#e6b800")
        add_btn("win_achievements", self.callbacks["achievements"], "violet")
        add_btn("menu_days_off", self.callbacks["days_off"], "#5dade2")
        add_btn("menu_subjects", self.callbacks["subjects"], "#e67e22")
        add_btn("menu_grades", self.callbacks["grades"], "#00b800")

        ctk.CTkFrame(content_frame, height=2, fg_color="gray80").pack(fill="x", pady=10)
        add_btn("btn_gen_full", self.callbacks["gen_full"])
        add_btn("btn_gen_new", self.callbacks["gen_new"])

        self.bind_id = self.winfo_toplevel().bind("<Button-1>", self.check_click_outside, add="+")

    def check_click_outside(self, event):
        if not self.is_open or self.ignore_click: return
        try:
            x = self.winfo_rootx();
            y = self.winfo_rooty();
            w = self.winfo_width();
            h = self.winfo_height()
        except:
            return
        if x <= event.x_root <= x + w and y <= event.y_root <= y + h: return
        self.close_panel()

    def open_panel(self):
        self.lift()
        self.is_open = True
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
        if abs(target - current) < 0.005: self.place(relx=target); return
        step = (target - current) * 0.25
        self.place(relx=current + step)
        self.after(16, lambda: self.animate(target))


# --- NOWA KLASA: CONTENT DRAWER (SZEROKA, WYŚRODKOWANA, PRZYKLEJONA DO PRAWEJ) ---
class ContentDrawer(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, corner_radius=20, border_width=1, border_color=("black", "white"),
                         fg_color=("gray90", "gray20"))

        self.is_open = False
        self.animation_id = None
        self.current_content = None

        # Startowa pozycja poza ekranem
        self.place(relx=1.0, rely=0.02, relheight=0.96, x=2000, anchor="ne")

        # Tworzymy szkielet RAZ przy inicjalizacji
        self._build_skeleton()

    def _build_skeleton(self):
        # NAGŁÓWEK (zostaje na zawsze)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.header_frame.pack(fill="x", padx=15, pady=10)

        self.btn_close = ctk.CTkButton(self.header_frame, text="✕", width=30, height=30,
                                       fg_color="transparent", text_color="gray", hover_color=("gray80", "gray30"),
                                       command=self.close_panel)
        self.btn_close.pack(side="right")

        # KONTENER (to do niego wkładamy panele)
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True, padx=5, pady=5)

    def set_content(self, content_class, **kwargs):
        # Czyścimy TYLKO zawartość kontenera, a nie sam kontener!
        for child in self.content_container.winfo_children():
            child.destroy()

        try:
            # Tworzymy nowy panel wewnątrz nienaruszonego kontenera
            self.current_content = content_class(self.content_container, **kwargs)
            self.current_content.pack(fill="both", expand=True)
            self.open_panel()
        except Exception as e:
            print(f"Error loading drawer content: {e}")

    def stop_animation(self):
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None

    def open_panel(self):
        self.stop_animation()
        self.is_open = True

        # Kluczowe dla Windows: odśwież geometrię
        self.winfo_toplevel().update_idletasks()

        self.tkraise()
        self.lift()

        # Obliczanie szerokości
        try:
            win_w = self.winfo_toplevel().winfo_width()
            if win_w <= 1: win_w = 1000
        except:
            win_w = 1000

        drawer_width = 600 if win_w >= 650 else int(win_w * 0.95)
        self.configure(width=drawer_width)

        # Wymuś przyjęcie szerokości przed animacją
        self.update_idletasks()
        self.animate(target_x=-20)

    def close_panel(self):
        self.stop_animation()
        self.is_open = False
        width = self.winfo_width()
        if width <= 1: width = 600
        self.animate(target_x=width + 50)

    def animate(self, target_x):
        try:
            current_x = int(self.place_info().get('x', 0))
        except:
            return

        if abs(target_x - current_x) < 2:
            self.place(relx=1.0, x=target_x, anchor="ne")
            self.animation_id = None
            return

        diff = target_x - current_x
        step = diff * 0.25
        if abs(step) < 1: step = 1 if diff > 0 else -1

        self.place(relx=1.0, x=current_x + step, anchor="ne")
        self.animation_id = self.after(16, lambda: self.animate(target_x))