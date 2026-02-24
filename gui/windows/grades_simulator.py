import customtkinter as ctk
import tkinter as tk
import uuid


class GradesSimulatorPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, storage, subject_id, close_callback=None):
        super().__init__(parent, fg_color="transparent", width=600)
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.subject_id = subject_id
        self.close_callback = close_callback

        self.real_modules = [dict(m) for m in self.storage.get_grade_modules(self.subject_id)]
        self.real_grades = [dict(g) for g in self.storage.get_grades(self.subject_id)]

        self.sim_modules = [dict(m) for m in self.real_modules]
        self.sim_grades = [dict(g) for g in self.real_grades]

        self.active_mod_entries = []
        self.active_grade_entries = []

        self._build_ui()
        self.render_tree()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # --- NAGŁÓWEK ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))

        ctk.CTkLabel(header, text=self.txt.get("win_simulator_title", "Interactive Simulator"),
                     font=("Arial", 24, "bold")).pack(side="left")

        ctk.CTkButton(header, text=self.txt.get("btn_close", "Back"), command=self.perform_close,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      hover_color=("gray80", "gray30"), height=32, corner_radius=20).pack(side="right")

        # --- PANEL WYNIKÓW (SCOREBOARD) ---
        score_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#2b2b2b", border_width=1, border_color="gray50")
        score_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))

        real_avg = self._calculate_real_average()
        real_txt = f"{real_avg:.1f}%" if real_avg is not None else "--"

        lbl_real_title = ctk.CTkLabel(score_frame, text=self.txt.get("lbl_real_avg", "Real Avg:"), font=("Arial", 16))
        lbl_real_title.pack(side="left", padx=(30, 5), pady=20)
        ctk.CTkLabel(score_frame, text=real_txt, font=("Arial", 18, "bold")).pack(side="left", padx=5, pady=20)

        lbl_sim_title = ctk.CTkLabel(score_frame, text=self.txt.get("lbl_sim_avg", "Simulated Avg:"),
                                     font=("Arial", 16))
        lbl_sim_title.pack(side="left", padx=(60, 5), pady=20)
        self.lbl_sim_score = ctk.CTkLabel(score_frame, text="--", font=("Arial", 26, "bold"), text_color="#3498db")
        self.lbl_sim_score.pack(side="left", padx=5, pady=20)

        # --- DRZEWO ---
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def render_tree(self):
        for widget in self.scroll_area.winfo_children():
            widget.destroy()

        self.active_mod_entries.clear()
        self.active_grade_entries.clear()

        # Render modułów
        for mod in self.sim_modules:
            self._render_module_block(mod)

        # Render "General" (jeśli są tam oceny)
        ungrouped = [g for g in self.sim_grades if not g.get("module_id")]
        if ungrouped:
            dummy_mod = {"id": None, "name": self.txt.get("cat_general", "General"), "weight": 0}
            self._render_module_block(dummy_mod, show_weight=False)

        # Przycisk "Dodaj Wirtualny Moduł" na samym dole (ZMIENIONY STYL)
        btn_add_mod = ctk.CTkButton(self.scroll_area, text=self.txt.get("btn_add_virt_mod", "+ Virtual Module"),
                                    height=36, corner_radius=20, font=("Arial", 14, "bold"),
                                    fg_color="transparent", border_width=1, border_color="#8e44ad",
                                    text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                                    command=self.add_virtual_module)
        btn_add_mod.pack(fill="x", pady=(15, 30), padx=5)

        self.recalculate_live()

    def _render_module_block(self, mod, show_weight=True):
        block = ctk.CTkFrame(self.scroll_area, fg_color="#333333", corner_radius=8)
        block.pack(fill="x", pady=8, padx=5)

        mod_header = ctk.CTkFrame(block, fg_color="transparent")
        mod_header.pack(fill="x", pady=8, padx=10)

        is_virt = mod.get("is_virtual", False)
        color = "#f39c12" if is_virt else "gray90"

        # Tytuł modułu
        ctk.CTkLabel(mod_header, text=mod["name"], font=("Arial", 18, "bold"), text_color=color).pack(side="left",
                                                                                                      pady=5)

        # Przycisk usuwania dla WIRTUALNYCH modułów (ZMIENIONY STYL)
        if is_virt:
            ctk.CTkButton(mod_header, text="X", width=28, height=28, corner_radius=20,
                          fg_color="transparent", border_width=1, border_color="#c0392b",
                          text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                          command=lambda mid=mod["id"]: self.remove_module(mid)).pack(side="left", padx=10)

        # Waga modułu
        if show_weight:
            ctk.CTkLabel(mod_header, text="%", font=("Arial", 14, "bold")).pack(side="right", padx=(5, 10))
            ent_mod_w = ctk.CTkEntry(mod_header, width=65, justify="center", font=("Arial", 14))
            ent_mod_w.insert(0, str(mod.get("weight", 0)))
            ent_mod_w.pack(side="right", padx=5)
            ent_mod_w.bind("<KeyRelease>", self.recalculate_live)

            self.active_mod_entries.append({"mod_id": mod["id"], "ent_weight": ent_mod_w})

        # Oceny wewnątrz modułu
        mod_grades = [g for g in self.sim_grades if g.get("module_id") == mod["id"]]
        for g in mod_grades:
            self._render_grade_row(block, g)

        # Przycisk dodawania wirtualnej oceny dla tego modułu (ZMIENIONY STYL)
        btn_box = ctk.CTkFrame(block, fg_color="transparent")
        btn_box.pack(fill="x", pady=(5, 15), padx=15)

        ctk.CTkButton(btn_box, text=self.txt.get("btn_add_virt_grade", "+ Virtual Grade"),
                      width=140, height=30, corner_radius=20,
                      fg_color="transparent", border_width=1, border_color="#e67e22",
                      text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                      command=lambda mid=mod["id"]: self.add_virtual_grade(mid)).pack(side="left")

    def _render_grade_row(self, parent_block, grade):
        row = ctk.CTkFrame(parent_block, fg_color="#262626", corner_radius=5)
        row.pack(fill="x", pady=4, padx=(15, 15))

        # --- LEWA STRONA (Opis) ---
        desc = grade.get("desc") or "Virtual"
        is_virt = grade.get("is_virtual", False)
        color = "#f39c12" if is_virt else "gray80"

        ctk.CTkLabel(row, text=desc, text_color=color, font=("Arial", 14)).pack(side="left", padx=15)

        # --- PRAWA STRONA (Kontrolki) ---
        controls_frame = ctk.CTkFrame(row, fg_color="transparent")
        controls_frame.pack(side="right", fill="y", pady=6, padx=10)

        top_ctrl = ctk.CTkFrame(controls_frame, fg_color="transparent")
        top_ctrl.pack(fill="x", anchor="e")

        bot_ctrl = ctk.CTkFrame(controls_frame, fg_color="transparent")
        bot_ctrl.pack(fill="x", anchor="e", pady=(6, 0))

        # [GÓRNY RZĄD] Przycisk Usuń (ZMIENIONY STYL)
        ctk.CTkButton(top_ctrl, text=self.txt.get("btn_remove", "X"), width=30, height=26, corner_radius=20,
                      fg_color="transparent", border_width=1, border_color="#c0392b",
                      text_color=("gray10", "gray90"), hover_color=("gray80", "gray30"),
                      command=lambda gid=grade["id"]: self.remove_grade(gid)).pack(side="right", padx=(15, 0))

        # [GÓRNY RZĄD] Waga
        ent_g_w = ctk.CTkEntry(top_ctrl, width=55, height=26, justify="center")
        ent_g_w.insert(0, str(grade.get("weight", 1)))
        ent_g_w.pack(side="right", padx=0)
        ctk.CTkLabel(top_ctrl, text=self.txt.get("lbl_w", "W:"), font=("Arial", 13)).pack(side="right", padx=5)
        ent_g_w.bind("<KeyRelease>", self.recalculate_live)

        # [GÓRNY RZĄD] Ocena końcowa (%)
        ent_g_val = ctk.CTkEntry(top_ctrl, width=60, height=26, justify="center", text_color="#2ecc71",
                                 font=("Arial", 13, "bold"))
        ent_g_val.insert(0, str(grade.get("value", 0)))
        ent_g_val.pack(side="right", padx=(0, 20))
        ctk.CTkLabel(top_ctrl, text=self.txt.get("lbl_val", "Val:"), font=("Arial", 13)).pack(side="right", padx=5)
        ent_g_val.bind("<KeyRelease>", self.recalculate_live)

        # [DOLNY RZĄD] Szybki przelicznik punktów
        ent_pts_max = ctk.CTkEntry(bot_ctrl, width=45, height=22, justify="center", placeholder_text="Max")
        ent_pts_max.pack(side="right", padx=(0, 65))

        ctk.CTkLabel(bot_ctrl, text="/", font=("Arial", 12, "bold")).pack(side="right", padx=3)

        ent_pts_got = ctk.CTkEntry(bot_ctrl, width=45, height=22, justify="center", placeholder_text="Got")
        ent_pts_got.pack(side="right", padx=0)

        ctk.CTkLabel(bot_ctrl, text=self.txt.get("lbl_pts_conv", "Pts ➡ %:"), font=("Arial", 11),
                     text_color="gray").pack(side="right", padx=5)

        def on_pts_change(event, eg=ent_pts_got, em=ent_pts_max, evalue=ent_g_val):
            try:
                g = float(eg.get())
                m = float(em.get())
                if m > 0:
                    perc = (g / m) * 100.0
                    evalue.delete(0, "end")
                    evalue.insert(0, f"{perc:.1f}")
                    self.recalculate_live()
            except ValueError:
                pass

        ent_pts_got.bind("<KeyRelease>", on_pts_change)
        ent_pts_max.bind("<KeyRelease>", on_pts_change)

        self.active_grade_entries.append({
            "grade_id": grade["id"],
            "module_id": grade.get("module_id"),
            "ent_val": ent_g_val,
            "ent_weight": ent_g_w
        })

    def perform_close(self):
        if self.close_callback: self.close_callback()

    # --- ZARZĄDZANIE WIRTUALNYMI DANYMI ---

    def add_virtual_module(self):
        new_mod = {
            "id": f"vmod_{uuid.uuid4().hex[:6]}",
            "name": "Virtual Module",
            "weight": 20,
            "is_virtual": True
        }
        self.sim_modules.append(new_mod)
        self.render_tree()

    def remove_module(self, mod_id):
        self.sim_modules = [m for m in self.sim_modules if m["id"] != mod_id]
        self.sim_grades = [g for g in self.sim_grades if g.get("module_id") != mod_id]
        self.render_tree()

    def add_virtual_grade(self, module_id):
        new_grade = {
            "id": f"virt_{uuid.uuid4().hex[:6]}",
            "module_id": module_id,
            "value": 100,
            "weight": 10,
            "desc": "Simulated",
            "is_virtual": True
        }
        self.sim_grades.append(new_grade)
        self.render_tree()

    def remove_grade(self, grade_id):
        self.sim_grades = [g for g in self.sim_grades if g["id"] != grade_id]
        self.render_tree()

    # --- KALKULACJE LIVE ---

    def recalculate_live(self, event=None):
        total_score = 0
        total_mod_weight = 0
        has_any_grade = False

        module_averages = {}
        live_mod_weights = {}

        for m_data in self.active_mod_entries:
            try:
                live_mod_weights[m_data["mod_id"]] = float(m_data["ent_weight"].get())
            except ValueError:
                live_mod_weights[m_data["mod_id"]] = 0.0

        grouped_grades = {}
        for g_data in self.active_grade_entries:
            mid = g_data["module_id"]
            try:
                val = float(g_data["ent_val"].get())
                w = float(g_data["ent_weight"].get())
            except ValueError:
                continue

            if mid not in grouped_grades:
                grouped_grades[mid] = []
            grouped_grades[mid].append({"value": val, "weight": w})

        for mid, grades in grouped_grades.items():
            sum_w = sum(g["weight"] for g in grades)
            if sum_w > 0:
                avg = sum(g["value"] * g["weight"] for g in grades) / sum_w
                module_averages[mid] = avg

        for mod in self.sim_modules:
            mid = mod["id"]
            if mid in module_averages:
                has_any_grade = True
                m_weight = live_mod_weights.get(mid, 0)
                total_score += module_averages[mid] * (m_weight / 100.0)
                total_mod_weight += m_weight

        if not has_any_grade and total_mod_weight == 0:
            self.lbl_sim_score.configure(text="--", text_color="gray")
        else:
            self.lbl_sim_score.configure(text=f"{total_score:.1f}%", text_color="#2ecc71")

    def _calculate_real_average(self):
        total_score = 0
        total_mod_weight = 0
        has_any = False

        for mod in self.real_modules:
            mod_grades = [g for g in self.real_grades if g.get("module_id") == mod["id"]]
            sum_w = sum(g.get("weight", 1) for g in mod_grades)
            if sum_w > 0:
                mod_avg = sum(g["value"] * g.get("weight", 1) for g in mod_grades) / sum_w
                has_any = True
                w = mod.get("weight", 0)
                total_score += mod_avg * (w / 100.0)
                total_mod_weight += w

        return total_score if (has_any or total_mod_weight > 0) else None