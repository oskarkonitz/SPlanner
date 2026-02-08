import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import sys
import os
import uuid
import json
from gui.theme_manager import apply_theme
from core.sound import SoundGenerator


class SettingsWindow:
    def __init__(self, parent, txt, btn_style, storage, app_version="1.0.0", callback_refresh=None):
        self.win = ctk.CTkToplevel(parent)
        self.txt = txt
        self.btn_style = btn_style
        self.storage = storage
        self.app_version = app_version
        self.callback_refresh = callback_refresh

        self.win.title(self.txt.get("win_settings_title", "Settings"))
        self.win.geometry("950x750")
        self.win.minsize(800, 600)

        # Pobieramy aktualne ustawienia z bazy
        self.current_settings = self.storage.get_settings()

        # --- ZMIENNE STANU ---
        self.var_lang = tk.StringVar(value=self.current_settings.get("lang", "en"))
        self.var_theme = tk.StringVar(value=self.current_settings.get("theme", "light"))
        self.var_badges = tk.StringVar(value=self.current_settings.get("badge_mode", "default"))
        self.var_switch_hour = tk.DoubleVar(value=float(self.current_settings.get("next_exam_switch_hour", 24)))

        # NOWE ZMIENNE AUDIO
        self.var_sound_enabled = tk.BooleanVar(value=self.current_settings.get("sound_enabled", True))
        self.var_sound_volume = tk.DoubleVar(value=self.current_settings.get("sound_volume", 0.5))

        # Grading System
        grad_sys = self.current_settings.get("grading_system", {})
        self.var_grade_mode = tk.StringVar(value=grad_sys.get("grade_mode", "percentage"))
        self.var_weight_mode = tk.StringVar(value=grad_sys.get("weight_mode", "percentage"))
        self.var_advanced_grading = tk.BooleanVar(value=grad_sys.get("advanced_mode", False))

        defaults = {"3.0": 50, "3.5": 60, "4.0": 70, "4.5": 80, "5.0": 90}
        saved_thresholds = grad_sys.get("thresholds", defaults)

        self.threshold_rows = []
        sorted_items = sorted(saved_thresholds.items(), key=lambda x: x[1])

        for grade_key, val in sorted_items:
            self.threshold_rows.append({
                'grade_var': tk.StringVar(value=str(grade_key)),
                'value_var': tk.StringVar(value=str(val))
            })

        # --- AUDIO LAB VARIABLES ---
        self.audio_steps = []
        self.sound_gen = SoundGenerator()

        self.saved_sounds = self.storage.get_custom_sounds()
        self.var_selected_sound_edit = tk.StringVar(value=self.txt.get("audio_new_sound", "New Sound"))
        self.var_sound_name = tk.StringVar(value="My Retro Sound")
        self.current_sound_id = None

        self.var_sound_timer = tk.StringVar(value=self.current_settings.get("sound_timer_finish") or "None")
        self.var_sound_ach = tk.StringVar(value=self.current_settings.get("sound_achievement") or "None")
        self.var_sound_all_done = tk.StringVar(value=self.current_settings.get("sound_all_done") or "None")

        # --- UKŁAD GŁÓWNY ---
        self.win.grid_columnconfigure(1, weight=1)
        self.win.grid_rowconfigure(0, weight=1)

        # 1. LEWY PASEK
        self.frame_nav = ctk.CTkFrame(self.win, corner_radius=0, width=200)
        self.frame_nav.grid(row=0, column=0, sticky="nsew")
        self.frame_nav.grid_rowconfigure(6, weight=1)

        self.btn_nav_gen = self._create_nav_btn("set_cat_general", 0, lambda: self.show_frame("general"))
        self.btn_nav_grad = self._create_nav_btn("set_cat_grading", 1, lambda: self.show_frame("grading"))
        self.btn_nav_plan = self._create_nav_btn("set_cat_planner", 2, lambda: self.show_frame("planner"))
        self.btn_nav_data = self._create_nav_btn("set_cat_data", 3, lambda: self.show_frame("data"))
        self.btn_nav_audio = self._create_nav_btn("set_cat_audio", 4, lambda: self.show_frame("audio"))

        # 2. PRAWY OBSZAR
        self.frame_content = ctk.CTkScrollableFrame(self.win, corner_radius=0, fg_color="transparent")
        self.frame_content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # 3. DOLNY PASEK
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
        self._init_audio_frame()

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
        btns = [self.btn_nav_gen, self.btn_nav_grad, self.btn_nav_plan, self.btn_nav_data, self.btn_nav_audio]
        for btn in btns:
            btn.configure(fg_color="transparent")

        if name == "general":
            self.btn_nav_gen.configure(fg_color=("gray85", "gray25"))
        elif name == "grading":
            self.btn_nav_grad.configure(fg_color=("gray85", "gray25"))
        elif name == "planner":
            self.btn_nav_plan.configure(fg_color=("gray85", "gray25"))
        elif name == "data":
            self.btn_nav_data.configure(fg_color=("gray85", "gray25"))
        elif name == "audio":
            self.btn_nav_audio.configure(fg_color=("gray85", "gray25"))

        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    # --- SEKCJE GUI ---

    def _init_general_frame(self):
        f = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        self.frames["general"] = f
        ctk.CTkLabel(f, text=self.txt.get("lang_label", "Language"), font=("Arial", 16, "bold")).pack(anchor="w",
                                                                                                      pady=(0, 10))
        lang_vals = ["en", "pl", "de", "es"]
        ctk.CTkSegmentedButton(f, values=lang_vals, variable=self.var_lang).pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(f, text=self.txt.get("lbl_theme", "Theme"), font=("Arial", 16, "bold")).pack(anchor="w",
                                                                                                  pady=(0, 10))
        ctk.CTkSegmentedButton(f, values=["light", "dark"], variable=self.var_theme).pack(anchor="w", pady=(0, 20))
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
        ctk.CTkLabel(f, text=self.txt.get("set_weight_sys", "Weight System"), font=("Arial", 16, "bold")).pack(
            anchor="w", pady=(0, 10))
        ctk.CTkRadioButton(f, text=self.txt.get("weight_sys_perc", "Percentage (e.g. 40%, 60%)"),
                           variable=self.var_weight_mode, value="percentage").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f, text=self.txt.get("weight_sys_num", "Numeric Weights (e.g. 1, 3)"),
                           variable=self.var_weight_mode, value="numeric").pack(anchor="w", pady=5)
        ctk.CTkFrame(f, height=2, fg_color=("gray70", "gray30")).pack(fill="x", pady=20)
        ctk.CTkLabel(f, text=self.txt.get("lbl_adv_grading", "Advanced Grading (Modules)"),
                     font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))
        ctk.CTkSwitch(f, text=self.txt.get("btn_enable", "Enable"), variable=self.var_advanced_grading).pack(anchor="w",
                                                                                                             pady=5)
        ctk.CTkLabel(f, text=self.txt.get("msg_adv_grading_note",
                                          "Allows grouping grades into modules (e.g. Lecture, Lab)."),
                     text_color="gray", font=("Arial", 11)).pack(anchor="w", pady=(0, 15))
        h_frame = ctk.CTkFrame(f, fg_color="transparent")
        h_frame.pack(fill="x", pady=(10, 5))
        ctk.CTkLabel(h_frame, text=self.txt.get("lbl_thresholds", "GPA Thresholds"), font=("Arial", 16, "bold")).pack(
            side="left")
        ctk.CTkButton(h_frame, text="+", width=30, height=25, fg_color="#2ecc71", hover_color="#27ae60",
                      command=self._add_threshold_row).pack(side="left", padx=10)
        self.thresholds_container = ctk.CTkFrame(f, fg_color="transparent")
        self.thresholds_container.pack(fill="x", pady=5)
        self._refresh_thresholds_ui()

    def _refresh_thresholds_ui(self):
        for widget in self.thresholds_container.winfo_children(): widget.destroy()
        if self.threshold_rows:
            header_f = ctk.CTkFrame(self.thresholds_container, fg_color="transparent")
            header_f.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(header_f, text="Grade Name", width=80, anchor="w", font=("Arial", 11, "bold")).pack(
                side="left", padx=5)
            ctk.CTkLabel(header_f, text="Min %", width=60, anchor="w", font=("Arial", 11, "bold")).pack(side="left",
                                                                                                        padx=5)
        for i, row_data in enumerate(self.threshold_rows):
            row_frame = ctk.CTkFrame(self.thresholds_container, fg_color="transparent")
            row_frame.pack(fill="x", pady=2)
            ctk.CTkEntry(row_frame, textvariable=row_data['grade_var'], width=80, justify="center").pack(side="left",
                                                                                                         padx=5)
            ctk.CTkEntry(row_frame, textvariable=row_data['value_var'], width=60, justify="center").pack(side="left",
                                                                                                         padx=5)
            ctk.CTkLabel(row_frame, text="%", text_color="gray").pack(side="left")
            ctk.CTkButton(row_frame, text="-", width=30, height=25, fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda idx=i: self._remove_threshold_row(idx)).pack(side="left", padx=15)

    def _add_threshold_row(self):
        self.threshold_rows.append({'grade_var': tk.StringVar(value=""), 'value_var': tk.StringVar(value="0")})
        self._refresh_thresholds_ui()

    def _remove_threshold_row(self, index):
        if 0 <= index < len(self.threshold_rows):
            self.threshold_rows.pop(index)
            self._refresh_thresholds_ui()

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
        ctk.CTkButton(f, text=self.txt.get("btn_clear_data", "Clear All Data"), fg_color="#e74c3c",
                      hover_color="#c0392b", command=self._request_clear_data).pack(anchor="w", pady=10)
        ctk.CTkLabel(f, text=self.txt.get("lbl_updates", "Updates"), font=("Arial", 16, "bold")).pack(anchor="w",
                                                                                                      pady=(20, 10))
        ctk.CTkButton(f, text=self.txt.get("menu_check_updates", "Check for Updates"), fg_color="transparent",
                      border_width=1, text_color=("gray10", "gray90"),
                      command=lambda: messagebox.showinfo(self.txt["msg_info"], self.txt.get("msg_latest_version",
                                                                                             "You have the latest version."))).pack(
            anchor="w", pady=10)
        ctk.CTkLabel(f, text=f"{self.txt.get('lbl_app_version', 'App Version')}: {self.app_version}",
                     text_color="gray").pack(side="bottom", anchor="w")

    # --- RETRO AUDIO LAB FRAME ---
    def _init_audio_frame(self):
        f = ctk.CTkFrame(self.frame_content, fg_color="transparent")
        self.frames["audio"] = f

        # HEADER + MASTER VOLUME
        top_panel = ctk.CTkFrame(f, fg_color="transparent")
        top_panel.pack(fill="x", pady=10)

        ctk.CTkLabel(top_panel, text=self.txt.get("audio_title", "🎹 Retro Audio Lab"), font=("Arial", 20, "bold")).pack(
            side="left")

        # Sekcja głośności
        vol_frame = ctk.CTkFrame(top_panel, fg_color="transparent")
        vol_frame.pack(side="right")

        ctk.CTkSwitch(vol_frame, text=self.txt.get("audio_enabled", "Sound ON"), variable=self.var_sound_enabled).pack(
            side="left", padx=10)

        ctk.CTkLabel(vol_frame, text=self.txt.get("audio_volume", "Volume:")).pack(side="left", padx=5)
        slider_vol = ctk.CTkSlider(vol_frame, width=100, from_=0.0, to=1.0, variable=self.var_sound_volume)
        slider_vol.pack(side="left")

        ctk.CTkLabel(f, text=self.txt.get("audio_desc", "Create 8-bit sound effects for timers and achievements."),
                     text_color="gray").pack(anchor="w", pady=(0, 20))

        # --- SEKCJA 1: BIBLIOTEKA ---
        lib_frame = ctk.CTkFrame(f, fg_color=("gray90", "gray20"))
        lib_frame.pack(fill="x", pady=10, padx=5)

        ctk.CTkLabel(lib_frame, text=self.txt.get("audio_select_label", "Select Sound to Edit:"),
                     font=("Arial", 12, "bold")).pack(side="left", padx=10)

        new_sound_txt = self.txt.get("audio_new_sound", "New Sound")
        sound_names = [new_sound_txt] + [s["name"] for s in self.saved_sounds]
        self.combo_sounds = ctk.CTkComboBox(lib_frame, values=sound_names, command=self._on_sound_select, width=200)
        self.combo_sounds.pack(side="left", padx=10, pady=10)

        ctk.CTkButton(lib_frame, text=self.txt.get("btn_delete", "Delete"), width=80, fg_color="#e74c3c",
                      hover_color="#c0392b",
                      command=self._delete_current_sound).pack(side="right", padx=10)

        # --- SEKCJA 2: EDYTOR (NAZWA + KROKI) ---
        edit_frame = ctk.CTkFrame(f, fg_color="transparent")
        edit_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(edit_frame, text=self.txt.get("audio_name_label", "Sound Name:")).pack(side="left", padx=5)
        ctk.CTkEntry(edit_frame, textvariable=self.var_sound_name, width=200).pack(side="left", padx=5)

        ctk.CTkButton(edit_frame, text=self.txt.get("btn_save", "Save Sound"), width=100,
                      command=self._save_sound_to_db, **self.btn_style).pack(side="left", padx=10)

        # Kontener na kroki sekwencera
        self.audio_steps_container = ctk.CTkFrame(f, fg_color="transparent")
        self.audio_steps_container.pack(fill="x", pady=10)

        if not self.audio_steps:
            self._add_audio_step(440, 0.2, "Square")

        # Pasek narzędzi
        tools_frame = ctk.CTkFrame(f, fg_color="transparent")
        tools_frame.pack(fill="x", pady=10)

        ctk.CTkButton(tools_frame, text=self.txt.get("audio_add_note", "+ Add Note"), width=100,
                      fg_color="#2ecc71", hover_color="#27ae60",
                      command=lambda: self._add_audio_step(440, 0.2, "Square")).pack(side="left", padx=5)

        ctk.CTkButton(tools_frame, text=self.txt.get("audio_play", "▶ Play Preview"), width=120,
                      fg_color="#3498db", hover_color="#2980b9",
                      command=self._generate_and_play).pack(side="left", padx=5)

        # --- SEKCJA 3: PRZYPISYWANIE ---
        ctk.CTkFrame(f, height=2, fg_color=("gray70", "gray30")).pack(fill="x", pady=20)
        ctk.CTkLabel(f, text=self.txt.get("audio_events_title", "Event Bindings"), font=("Arial", 16, "bold")).pack(
            anchor="w", pady=(0, 10))

        assign_frame = ctk.CTkFrame(f, fg_color="transparent")
        assign_frame.pack(fill="x", pady=5)

        assign_options = ["None"] + [s["name"] for s in self.saved_sounds]

        # Timer
        row_t = ctk.CTkFrame(assign_frame, fg_color="transparent")
        row_t.pack(fill="x", pady=2)
        ctk.CTkLabel(row_t, text=self.txt.get("audio_event_timer", "Timer Finish:"), width=150, anchor="w").pack(
            side="left")
        self.combo_assign_timer = ctk.CTkComboBox(row_t, values=assign_options, variable=self.var_sound_timer)
        self.combo_assign_timer.pack(side="left")

        # Achievement
        row_a = ctk.CTkFrame(assign_frame, fg_color="transparent")
        row_a.pack(fill="x", pady=2)
        ctk.CTkLabel(row_a, text=self.txt.get("audio_event_ach", "Achievement Unlock:"), width=150, anchor="w").pack(
            side="left")
        self.combo_assign_ach = ctk.CTkComboBox(row_a, values=assign_options, variable=self.var_sound_ach)
        self.combo_assign_ach.pack(side="left")

        # All Tasks Done
        row_d = ctk.CTkFrame(assign_frame, fg_color="transparent")
        row_d.pack(fill="x", pady=2)
        ctk.CTkLabel(row_d, text=self.txt.get("audio_event_done", "All Tasks Done:"), width=150, anchor="w").pack(
            side="left")
        self.combo_assign_done = ctk.CTkComboBox(row_d, values=assign_options, variable=self.var_sound_all_done)
        self.combo_assign_done.pack(side="left")

    # --- LOGIKA AUDIO UI ---

    def _on_sound_select(self, choice):
        new_txt = self.txt.get("audio_new_sound", "New Sound")
        if choice == new_txt:
            self.current_sound_id = None
            self.var_sound_name.set("My Retro Sound")
            self.audio_steps = []
            self._add_audio_step(440, 0.2, "Square")
        else:
            sound = next((s for s in self.saved_sounds if s["name"] == choice), None)
            if sound:
                self.current_sound_id = sound["id"]
                self.var_sound_name.set(sound["name"])
                self.audio_steps = []
                for step in sound["steps"]:
                    self._add_audio_step(step['freq'], step['dur'], step['type'])

        self._refresh_audio_ui()

    def _add_audio_step(self, freq_val, dur_val, wave_val):
        step_data = {
            'freq': tk.DoubleVar(value=freq_val),
            'dur': tk.DoubleVar(value=dur_val),
            'type': tk.StringVar(value=wave_val)
        }
        self.audio_steps.append(step_data)
        self._refresh_audio_ui()

    def _remove_audio_step(self, index):
        if 0 <= index < len(self.audio_steps):
            self.audio_steps.pop(index)
            self._refresh_audio_ui()

    def _refresh_audio_ui(self):
        for w in self.audio_steps_container.winfo_children():
            w.destroy()

        for i, step in enumerate(self.audio_steps):
            row = ctk.CTkFrame(self.audio_steps_container, fg_color=("gray90", "gray20"), corner_radius=6)
            row.pack(fill="x", pady=4)

            ctk.CTkLabel(row, text=f"#{i + 1}", width=30, font=("Arial", 12, "bold")).pack(side="left", padx=5)

            f_frame = ctk.CTkFrame(row, fg_color="transparent")
            f_frame.pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkLabel(f_frame, text=self.txt.get("audio_pitch", "Pitch"), font=("Arial", 10)).pack(anchor="w")
            lbl_hz = ctk.CTkLabel(f_frame, text=f"{int(step['freq'].get())} Hz", font=("Arial", 10, "bold"), width=50)
            lbl_hz.pack(side="right")
            s_freq = ctk.CTkSlider(f_frame, from_=50, to=1500, variable=step['freq'], number_of_steps=145,
                                   command=lambda v, l=lbl_hz: l.configure(text=f"{int(v)} Hz"))
            s_freq.pack(fill="x")

            d_frame = ctk.CTkFrame(row, fg_color="transparent")
            d_frame.pack(side="left", padx=10, fill="x", expand=True)
            ctk.CTkLabel(d_frame, text=self.txt.get("audio_duration", "Duration"), font=("Arial", 10)).pack(anchor="w")
            lbl_dur = ctk.CTkLabel(d_frame, text=f"{step['dur'].get():.1f} s", font=("Arial", 10, "bold"), width=40)
            lbl_dur.pack(side="right")
            s_dur = ctk.CTkSlider(d_frame, from_=0.1, to=1.0, variable=step['dur'], number_of_steps=9,
                                  command=lambda v, l=lbl_dur: l.configure(text=f"{v:.1f} s"))
            s_dur.pack(fill="x")

            ctk.CTkOptionMenu(row, variable=step['type'], values=["Square", "Sawtooth", "Sine", "Noise"],
                              width=100).pack(side="left", padx=10)
            ctk.CTkButton(row, text="X", width=30, fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda idx=i: self._remove_audio_step(idx)).pack(side="left", padx=10)

    def _generate_and_play(self):
        if not self.audio_steps: return
        current_vol = self.var_sound_volume.get()
        self.sound_gen.clear()
        for step in self.audio_steps:
            self.sound_gen.add_note(step['freq'].get(), step['dur'].get(), step['type'].get(),
                                    master_volume=current_vol)
        self.sound_gen.play()

    def _save_sound_to_db(self):
        name = self.var_sound_name.get().strip()
        if not name:
            messagebox.showwarning(self.txt.get("msg_error", "Error"),
                                   self.txt.get("msg_empty_name", "Name cannot be empty"))
            return

        plain_steps = []
        for s in self.audio_steps:
            plain_steps.append({
                'freq': s['freq'].get(),
                'dur': s['dur'].get(),
                'type': s['type'].get()
            })

        sound_id = self.current_sound_id or f"snd_{uuid.uuid4().hex[:8]}"

        sound_data = {
            "id": sound_id,
            "name": name,
            "steps": plain_steps
        }

        self.storage.add_custom_sound(sound_data)
        self.current_sound_id = sound_id

        self.saved_sounds = self.storage.get_custom_sounds()
        new_txt = self.txt.get("audio_new_sound", "New Sound")
        names = [new_txt] + [s["name"] for s in self.saved_sounds]

        self.combo_sounds.configure(values=names)
        self.combo_sounds.set(name)

        assign_opts = ["None"] + [s["name"] for s in self.saved_sounds]
        self.combo_assign_timer.configure(values=assign_opts)
        self.combo_assign_ach.configure(values=assign_opts)
        self.combo_assign_done.configure(values=assign_opts)

        messagebox.showinfo(self.txt.get("msg_success", "Success"), self.txt.get("msg_saved", "Saved!"))

    def _delete_current_sound(self):
        if not self.current_sound_id: return
        if messagebox.askyesno(self.txt.get("msg_confirm", "Confirm"), self.txt.get("msg_delete_confirm", "Delete?")):
            self.storage.delete_custom_sound(self.current_sound_id)
            self.saved_sounds = self.storage.get_custom_sounds()

            new_txt = self.txt.get("audio_new_sound", "New Sound")
            self._on_sound_select(new_txt)

            names = [new_txt] + [s["name"] for s in self.saved_sounds]
            self.combo_sounds.configure(values=names)

            assign_opts = ["None"] + [s["name"] for s in self.saved_sounds]
            self.combo_assign_timer.configure(values=assign_opts)
            self.combo_assign_ach.configure(values=assign_opts)
            self.combo_assign_done.configure(values=assign_opts)

    # --- KONIEC AUDIO ---

    def _request_clear_data(self):
        messagebox.showinfo(self.txt["msg_info"],
                            self.txt.get("msg_use_clear_menu", "Please use the 'File -> Clear Data' menu."))

    def save_all(self):
        old_lang = self.current_settings.get("lang", "en")
        new_lang = self.var_lang.get()
        lang_changed = old_lang != new_lang

        # Zapis standardowych
        self.storage.update_setting("lang", new_lang)
        self.storage.update_setting("theme", self.var_theme.get())
        self.storage.update_setting("badge_mode", self.var_badges.get())
        self.storage.update_setting("next_exam_switch_hour", int(self.var_switch_hour.get()))

        # Zapis głośności
        self.storage.update_setting("sound_enabled", self.var_sound_enabled.get())
        self.storage.update_setting("sound_volume", self.var_sound_volume.get())

        # Zapis przypisań dźwięków
        t_name = self.var_sound_timer.get()
        a_name = self.var_sound_ach.get()
        d_name = self.var_sound_all_done.get()

        t_id = next((s["id"] for s in self.saved_sounds if s["name"] == t_name), None)
        a_id = next((s["id"] for s in self.saved_sounds if s["name"] == a_name), None)
        d_id = next((s["id"] for s in self.saved_sounds if s["name"] == d_name), None)

        self.storage.update_setting("sound_timer_finish", t_id)
        self.storage.update_setting("sound_achievement", a_id)
        self.storage.update_setting("sound_all_done", d_id)

        # Zbieranie progów
        new_thresholds = {}
        try:
            for row in self.threshold_rows:
                g_name = row['grade_var'].get().strip()
                g_val_str = row['value_var'].get().strip()
                if not g_name: continue
                val = int(g_val_str)
                if val < 0 or val > 100: raise ValueError
                new_thresholds[g_name] = val
        except ValueError:
            messagebox.showwarning(self.txt.get("msg_error", "Error"),
                                   "Threshold percentages must be integers (0-100).")
            return

        new_grading = {
            "grade_mode": self.var_grade_mode.get(),
            "weight_mode": self.var_weight_mode.get(),
            "pass_threshold": 50,
            "advanced_mode": self.var_advanced_grading.get(),
            "thresholds": new_thresholds
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