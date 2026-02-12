import customtkinter as ctk

class StaticAchievementItem(ctk.CTkFrame):
    def __init__(self, parent, icon, title, desc, is_unlocked, corner_text=None, *args, **kwargs):
        super().__init__(parent, fg_color="transparent", *args, **kwargs)

        mode = ctk.get_appearance_mode()
        bg_color = ("gray90", "gray20") if is_unlocked else ("gray95", "gray15")

        main_frame = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=10)
        main_frame.pack(fill="x", pady=2)

        display_icon = icon if is_unlocked else "🔒"
        status_color = "#27ae60" if is_unlocked else "gray"
        desc_color = "gray30" if mode == "Light" else "gray70"

        content = ctk.CTkFrame(main_frame, fg_color="transparent")
        content.pack(padx=10, pady=10, fill="x")

        ctk.CTkLabel(content, text=display_icon, font=("Arial", 30)).pack(side="left", padx=(0, 15))

        text_frame = ctk.CTkFrame(content, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(text_frame, text=title, font=("Arial", 14, "bold"), text_color=status_color, anchor="w").pack(
            fill="x")
        ctk.CTkLabel(text_frame, text=desc, font=("Arial", 12), text_color=desc_color, anchor="w", wraplength=350).pack(
            fill="x")

        # --- NOWOŚĆ: Wyświetlanie tekstu w prawym górnym rogu ---
        # TWORZYMY NA KOŃCU, ŻEBY BYŁO NA WIERZCHU I DAJEMY LIFT
        if corner_text:
            lbl_corner = ctk.CTkLabel(main_frame, text=corner_text, font=("Arial", 11, "bold"), text_color="#3498db")
            lbl_corner.place(relx=0.97, rely=0.08, anchor="ne")
            lbl_corner.lift()
        # --------------------------------------------------------


class AccordionItem(ctk.CTkFrame):
    def __init__(self, parent, txt, icon, title, level_text, details_list, is_unlocked, corner_text=None, *args,
                 **kwargs):
        super().__init__(parent, fg_color="transparent", *args, **kwargs)
        self.txt = txt
        self.details_list = details_list
        self.is_expanded = False

        self.bg_color = ("gray90", "gray20") if is_unlocked else ("gray95", "gray15")
        self.hover_color = ("gray85", "gray25")

        self.main_frame = ctk.CTkFrame(self, fg_color=self.bg_color, corner_radius=10)
        self.main_frame.pack(fill="x", pady=2)

        self.header_btn = ctk.CTkButton(
            self.main_frame, text="", fg_color="transparent", hover_color=self.hover_color,
            height=60, command=self.toggle
        )
        self.header_btn.pack(fill="x")

        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.place(relx=0.02, rely=0.1, relwidth=0.96, relheight=0.8)

        display_icon = icon if is_unlocked else "🔒"
        status_color = "#27ae60" if is_unlocked else "gray"

        lbl_icon = ctk.CTkLabel(self.content_frame, text=display_icon, font=("Arial", 30))
        lbl_icon.pack(side="left", padx=10)

        info_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        full_title = f"{title} {level_text}" if level_text else title
        lbl_title = ctk.CTkLabel(info_frame, text=full_title, font=("Arial", 14, "bold"), text_color=status_color,
                                 anchor="w")
        lbl_title.pack(fill="x")

        lbl_hint = ctk.CTkLabel(info_frame, text=self.txt.get("ach_click_to_expand", "Click to expand"),
                                font=("Arial", 10), text_color="gray", anchor="w")
        lbl_hint.pack(fill="x")

        for w in [lbl_icon, info_frame, lbl_title, lbl_hint, self.content_frame]:
            w.bind("<Button-1>", lambda e: self.toggle())

        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")

        # --- NOWOŚĆ: Wyświetlanie tekstu w prawym górnym rogu ---
        # TWORZYMY NA KOŃCU I LIFT
        if corner_text:
            lbl_corner = ctk.CTkLabel(self.main_frame, text=corner_text, font=("Arial", 11, "bold"),
                                      text_color="#3498db")
            lbl_corner.place(relx=0.97, rely=0.08, anchor="ne")
            lbl_corner.lift()
        # --------------------------------------------------------

    def toggle(self):
        if self.is_expanded:
            self.details_frame.pack_forget()
            self.is_expanded = False
        else:
            self.build_details()
            self.details_frame.pack(fill="x", padx=10, pady=(0, 10))
            self.is_expanded = True

    def build_details(self):
        for w in self.details_frame.winfo_children(): w.destroy()
        for d_title, d_desc, d_unlocked in self.details_list:
            row = ctk.CTkFrame(self.details_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            icon = "✅" if d_unlocked else "🔒"
            col = "#27ae60" if d_unlocked else "gray"
            ctk.CTkLabel(row, text=icon, width=30).pack(side="left")
            ctk.CTkLabel(row, text=d_title, font=("Arial", 12, "bold"), text_color=col, anchor="w", width=150).pack(
                side="left")
            ctk.CTkLabel(row, text=d_desc, font=("Arial", 12), text_color="gray", anchor="w", wraplength=250).pack(
                side="left", fill="x", expand=True)