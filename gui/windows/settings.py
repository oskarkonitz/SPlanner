import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import sys
import os
from gui.theme_manager import apply_theme


class SettingsWindow:
    def __init__(self, parent, txt, btn_style, storage, app_version="1.0.0", callback_refresh=None):
        self.win = ctk.CTkToplevel(parent)
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.app_version = app_version  # ZAPISUJEMY WERSJĘ
        self.callback_refresh = callback_refresh

        self.win.title(self.txt.get("win_settings_title", "Settings"))
        self.win.geometry("800x600")
        self.win.minsize(700, 500)

        # Pobieramy aktualne ustawienia z bazy
        self.current_settings = self.storage.get_settings()

        # --- ZMIENNE STANU (Bufor przed zapisem) ---
        self.var_lang = tk.StringVar(value=self.current_settings.get("lang", "en"))
        self.var_theme = tk.StringVar(value=self.current_settings.get("theme", "light"))
        self.var_badges = tk.StringVar(value=self.current_settings.get("badge_mode", "default"))
        self.var_switch_hour = tk.DoubleVar(value=float(self.current_settings.get("next_exam_switch_hour", 24)))

        # Grading System
        grad_sys = self.current_settings.get("grading_system", {})
        self.var_grade_mode = tk.StringVar(value=grad_sys.get("grade_mode", "percentage"))
        self.var_weight_mode = tk.StringVar(value=grad_sys.get("weight_mode", "percentage"))

        # --- UKŁAD GŁÓWNY ---
        self.win.grid_columnconfigure(1, weight=1)
        self.win.grid_rowconfigure(0, weight=1)

        # 1. LEWY PASEK (KATEGORIE)
        self.frame_nav = ctk.CTkFrame(self.win, corner_radius=0, width=200)
        self.frame_nav.grid(row=0, column=0, sticky="nsew")
        self.frame_nav.grid_rowconfigure(5, weight=1)  # Spacer

        self.btn_nav_gen = self._create_nav_btn("set_cat_general", 0, lambda: self.show_frame("general"))
        self.btn_nav_grad = self._create_nav_btn("set_cat_grading", 1, lambda: self.show_frame("grading"))
        self.btn_nav_plan = self._create_nav_btn("set_cat_planner", 2, lambda: self.show_frame("planner"))
        self.btn_nav_data = self._create_nav_btn("set_cat_data", 3, lambda: self.show_frame("data"))

        # 2. PRAWY OBSZAR (ZAWARTOŚĆ)
        self.frame_content = ctk.CTkFrame(self.win, corner_radius=0, fg_color="transparent")
        self.frame_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # 3. DOLNY PASEK (ZAPISZ)
        self.frame_footer = ctk.CTkFrame(self.win, height=50, corner_radius=0)
        self.frame_footer.grid(row=1, column=0, columnspan=2, sticky="ew")

        ctk.CTkButton(self.frame_footer, text=self.txt.get("btn_save_changes", "Save Changes"),
                      command=self.save_all, **self.btn_style).pack(side="right", padx=20, pady=10)

        ctk.CTkButton(self.frame_footer, text=self.txt.get("btn_cancel", "Cancel"),
                      command=self.win.destroy,
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90")).pack(side="right",
                                                                                                    padx=10, pady=10)

        # Inicjalizacja ramek
        self.frames = {}
        self._init_general_frame()
        self._init_grading_frame()
        self._init_planner_frame()
        self._init_data_frame()

        # Pokaż domyślną
        self.show_frame("general")

    def _create_nav_btn(self, key, row, cmd):
        text = self.txt.get(key, key)
        btn = ctk.CTkButton(self.frame_nav, text=text, command=cmd,
                            fg_color="transparent", text_color=("gray10", "gray90"),
                            anchor="w", height=40, font=("Arial", 13, "bold"))
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=5)
        return btn

    def show_frame(self, name):
        # Reset kolorów przycisków
        for btn in [self.btn_nav_gen, self.btn_nav_grad, self.btn_nav_plan, self.btn_nav_data]:
            btn.configure(fg_color="transparent")

        # Podświetl aktywny
        if name == "general":
            self.btn_nav_gen.configure(fg_color=("gray85", "gray25"))
        elif name == "grading":
            self.btn_nav_grad.configure(fg_color=("gray85", "gray25"))
        elif name == "planner":
            self.btn_nav_plan.configure(fg_color=("gray85", "gray25"))
        elif name == "data":
            self.btn_nav_data.configure(fg_color=("gray85", "gray25"))

        # Przełącz ramkę
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    # --- KONSTRUKCJA SEKCJI ---

    def _init_general_frame(self):
        f = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        self.frames["general"] = f

        # Language
        ctk.CTkLabel(f, text=self.txt.get("lang_label", "Language"), font=("Arial", 16, "bold")).pack(anchor="w",
                                                                                                      pady=(0, 10))
        lang_vals = ["en", "pl", "de", "es"]
        ctk.CTkSegmentedButton(f, values=lang_vals, variable=self.var_lang).pack(anchor="w", pady=(0, 20))

        # Theme
        ctk.CTkLabel(f, text=self.txt.get("lbl_theme", "Theme"), font=("Arial", 16, "bold")).pack(anchor="w",
                                                                                                  pady=(0, 10))
        ctk.CTkSegmentedButton(f, values=["light", "dark"], variable=self.var_theme).pack(anchor="w", pady=(0, 20))

        # Badges
        ctk.CTkLabel(f, text=self.txt.get("lbl_badges", "Notification Badges"), font=("Arial", 16, "bold")).pack(
            anchor="w", pady=(0, 10))
        ctk.CTkRadioButton(f, text=self.txt.get("badge_default", "Default (Count)"), variable=self.var_badges,
                           value="default").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f, text=self.txt.get("badge_dot", "Compact (Dot)"), variable=self.var_badges,
                           value="dot").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f, text=self.txt.get("badge_off", "Disabled"), variable=self.var_badges, value="off").pack(
            anchor="w", pady=5)

    def _init_grading_frame(self):
        f = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        self.frames["grading"] = f

        # Grade Scale
        ctk.CTkLabel(f, text=self.txt.get("set_grade_scale", "Grade Scale"), font=("Arial", 16, "bold")).pack(
            anchor="w", pady=(0, 10))

        ctk.CTkRadioButton(f, text=self.txt.get("grade_scale_perc", "Percentage (0-100%)"),
                           variable=self.var_grade_mode, value="percentage").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f, text=self.txt.get("grade_scale_2_5", "Numeric (2.0 - 5.0)"), variable=self.var_grade_mode,
                           value="2-5").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f, text=self.txt.get("grade_scale_1_6", "Numeric (1 - 6)"), variable=self.var_grade_mode,
                           value="1-6").pack(anchor="w", pady=5)

        ctk.CTkLabel(f, text=self.txt.get("msg_grade_scale_note", "Note: Affects display and validation."),
                     text_color="gray", font=("Arial", 11)).pack(anchor="w", pady=(0, 20))

        # Weight System
        ctk.CTkLabel(f, text=self.txt.get("set_weight_sys", "Weight System"), font=("Arial", 16, "bold")).pack(
            anchor="w", pady=(0, 10))

        ctk.CTkRadioButton(f, text=self.txt.get("weight_sys_perc", "Percentage (e.g. 40%, 60%)"),
                           variable=self.var_weight_mode, value="percentage").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f, text=self.txt.get("weight_sys_num", "Numeric Weights (e.g. 1, 3)"),
                           variable=self.var_weight_mode, value="numeric").pack(anchor="w", pady=5)

    def _init_planner_frame(self):
        f = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        self.frames["planner"] = f

        ctk.CTkLabel(f, text=self.txt.get("lbl_switch_time", "Exam Switch Time (Next Day)"),
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))

        self.lbl_slider = ctk.CTkLabel(f, text=f"{int(self.var_switch_hour.get())}:00")
        self.lbl_slider.pack(anchor="w")

        slider = ctk.CTkSlider(f, from_=12, to=24, number_of_steps=12, variable=self.var_switch_hour,
                               command=lambda v: self.lbl_slider.configure(text=f"{int(v)}:00"))
        slider.pack(anchor="w", fill="x", pady=5)

        ctk.CTkLabel(f, text=self.txt.get("msg_switch_time_note", "Hour to switch 'Nearest Exam' view."),
                     text_color="gray", font=("Arial", 11)).pack(anchor="w")

    def _init_data_frame(self):
        f = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        self.frames["data"] = f

        ctk.CTkLabel(f, text=self.txt.get("lbl_data_mgmt", "Data Management"), font=("Arial", 16, "bold")).pack(
            anchor="w", pady=(0, 10))

        ctk.CTkButton(f, text=self.txt.get("btn_clear_data", "Clear All Data"),
                      fg_color="#e74c3c", hover_color="#c0392b",
                      command=self._request_clear_data).pack(anchor="w", pady=10)

        ctk.CTkLabel(f, text=self.txt.get("lbl_updates", "Updates"), font=("Arial", 16, "bold")).pack(anchor="w",
                                                                                                      pady=(20, 10))

        ctk.CTkButton(f, text=self.txt.get("menu_check_updates", "Check for Updates"),
                      fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
                      command=lambda: messagebox.showinfo(self.txt["msg_info"], self.txt.get("msg_latest_version",
                                                                                             "You have the latest version."))).pack(
            anchor="w", pady=10)

        # UŻYCIE FAKTYCZNEJ WERSJI
        ver_txt = f"{self.txt.get('lbl_app_version', 'App Version')}: {self.app_version}"
        ctk.CTkLabel(f, text=ver_txt, text_color="gray").pack(side="bottom", anchor="w")

    def _request_clear_data(self):
        messagebox.showinfo(self.txt["msg_info"],
                            self.txt.get("msg_use_clear_menu", "Please use the 'File -> Clear Data' menu."))

    def save_all(self):
        old_lang = self.current_settings.get("lang", "en")
        new_lang = self.var_lang.get()
        lang_changed = old_lang != new_lang

        self.storage.update_setting("lang", new_lang)
        self.storage.update_setting("theme", self.var_theme.get())
        self.storage.update_setting("badge_mode", self.var_badges.get())
        self.storage.update_setting("next_exam_switch_hour", int(self.var_switch_hour.get()))

        new_grading = {
            "grade_mode": self.var_grade_mode.get(),
            "weight_mode": self.var_weight_mode.get(),
            "pass_threshold": 50
        }
        self.storage.update_setting("grading_system", new_grading)

        if self.callback_refresh:
            self.callback_refresh()

        messagebox.showinfo(self.txt.get("msg_success", "Success"),
                            self.txt.get("msg_settings_saved", "Settings saved successfully."))

        if lang_changed:
            if messagebox.askyesno(self.txt.get("title_restart", "Restart"),
                                   self.txt.get("msg_lang_restart", "Restart application now?")):
                self.win.destroy()
                os.execl(sys.executable, sys.executable, *sys.argv)

        self.win.destroy()