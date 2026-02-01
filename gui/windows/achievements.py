import customtkinter as ctk
import tkinter as tk
from datetime import date
from core.planner import date_format
from core.storage import save
import random
import math


# --- KLASA CZĄSTECZKI ---
class Particle:
    def __init__(self, canvas, x, y, color_palette):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.color = random.choice(color_palette)
        self.size = random.randint(2, 5)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 7)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.gravity = 0.15
        self.life = random.randint(80, 150)
        self.id = self.canvas.create_oval(x - self.size, y - self.size, x + self.size, y + self.size,
                                          fill=self.color, outline="")

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.canvas.coords(self.id, self.x - self.size, self.y - self.size, self.x + self.size, self.y + self.size)
        self.life -= 1
        if self.life < 20: self.size *= 0.9

    def is_alive(self): return self.life > 0


# --- MANAGER Z KOLEJKĄ POWIADOMIEŃ ---
class AchievementManager:
    def __init__(self, parent_window, txt, data):
        self.parent = parent_window
        self.txt = txt
        self.data = data
        self.notification_queue = []
        self.is_showing_popup = False

        if "achievements" not in self.data:
            self.data["achievements"] = []
        if "global_stats" not in self.data:
            self.data["global_stats"] = {
                "topics_done": 0, "notes_added": 0, "exams_added": 0,
                "days_off": 0, "pomodoro_sessions": 0, "activity_started": False,
                "had_overdue": False
            }

        self.definitions = [
            ("first_step", "👶", "ach_first_step", "ach_desc_first_step", self._check_first_step, 1),
            ("clean_sheet", "🧹", "ach_clean_sheet", "ach_desc_clean_sheet", self._check_clean_sheet, None),
            ("balance", "🏖️", "ach_balance", "ach_desc_balance", self._check_balance, 1),
            ("balance_2", "🏖️", "ach_balance_2", "ach_desc_balance_2", self._check_balance, 3),
            ("balance_3", "🏖️", "ach_balance_3", "ach_desc_balance_3", self._check_balance, 7),
            ("balance_4", "🏖️", "ach_balance_4", "ach_desc_balance_4", self._check_balance, 14),
            ("balance_5", "🏖️", "ach_balance_5", "ach_desc_balance_5", self._check_balance, 20),
            ("balance_6", "🏖️", "ach_balance_6", "ach_desc_balance_6", self._check_balance, 60),
            ("balance_7", "🏖️", "ach_balance_7", "ach_desc_balance_7", self._check_balance, 360),
            ("scribe_1", "✍", "ach_scribe_1", "ach_desc_scribe_1", self._check_scribe, 5),
            ("scribe_2", "✍", "ach_scribe_2", "ach_desc_scribe_2", self._check_scribe, 10),
            ("scribe_3", "✍", "ach_scribe_3", "ach_desc_scribe_3", self._check_scribe, 25),
            ("scribe_4", "✍", "ach_scribe_4", "ach_desc_scribe_4", self._check_scribe, 50),
            ("scribe_5", "✍", "ach_scribe_5", "ach_desc_scribe_5", self._check_scribe, 100),
            ("scribe_6", "✍", "ach_scribe_6", "ach_desc_scribe_6", self._check_scribe, 250),
            ("scribe_7", "✍", "ach_scribe_7", "ach_desc_scribe_7", self._check_scribe, 500),
            ("scribe_8", "✍", "ach_scribe_8", "ach_desc_scribe_8", self._check_scribe, 1000),
            ("scribe_9", "✍", "ach_scribe_9", "ach_desc_scribe_9", self._check_scribe, 2000),
            ("encyclopedia_1", "📚", "ach_encyclopedia_1", "ach_desc_encyclopedia_1", self._check_encyclopedia, 10),
            ("encyclopedia_2", "📚", "ach_encyclopedia_2", "ach_desc_encyclopedia_2", self._check_encyclopedia, 25),
            ("encyclopedia_3", "📚", "ach_encyclopedia_3", "ach_desc_encyclopedia_3", self._check_encyclopedia, 50),
            ("encyclopedia_4", "📚", "ach_encyclopedia_4", "ach_desc_encyclopedia_4", self._check_encyclopedia, 100),
            ("encyclopedia_5", "📚", "ach_encyclopedia_5", "ach_desc_encyclopedia_5", self._check_encyclopedia, 200),
            ("encyclopedia_6", "📚", "ach_encyclopedia_6", "ach_desc_encyclopedia_6", self._check_encyclopedia, 250),
            ("encyclopedia_7", "📚", "ach_encyclopedia_7", "ach_desc_encyclopedia_7", self._check_encyclopedia, 500),
            ("encyclopedia_8", "📚", "ach_encyclopedia_8", "ach_desc_encyclopedia_8", self._check_encyclopedia, 1000),
            ("encyclopedia_9", "📚", "ach_encyclopedia_9", "ach_desc_encyclopedia_9", self._check_encyclopedia, 2000),
            ("time_lord_1", "🍅", "ach_time_lord_1", "ach_desc_time_lord_1", self._check_time_lord, 5),
            ("time_lord_2", "🍅", "ach_time_lord_2", "ach_desc_time_lord_2", self._check_time_lord, 10),
            ("time_lord_3", "🍅", "ach_time_lord_3", "ach_desc_time_lord_3", self._check_time_lord, 25),
            ("time_lord_4", "🍅", "ach_time_lord_4", "ach_desc_time_lord_4", self._check_time_lord, 50),
            ("time_lord_5", "🍅", "ach_time_lord_5", "ach_desc_time_lord_5", self._check_time_lord, 100),
            ("time_lord_6", "🍅", "ach_time_lord_6", "ach_desc_time_lord_6", self._check_time_lord, 500),
            ("time_lord_7", "🍅", "ach_time_lord_7", "ach_desc_time_lord_7", self._check_time_lord, 1000),
            ("session_master_1", "🎓", "ach_session_master_1", "ach_desc_session_master_1", self._check_session_master,
             1),
            ("session_master_2", "🎓", "ach_session_master_2", "ach_desc_session_master_2", self._check_session_master,
             3),
            ("session_master_3", "🎓", "ach_session_master_3", "ach_desc_session_master_3", self._check_session_master,
             5),
            ("session_master_4", "🎓", "ach_session_master_4", "ach_desc_session_master_4", self._check_session_master,
             10),
            ("session_master_5", "🎓", "ach_session_master_5", "ach_desc_session_master_5", self._check_session_master,
             20),
            ("session_master_6", "🎓", "ach_session_master_6", "ach_desc_session_master_6", self._check_session_master,
             100),
            ("session_master_7", "🎓", "ach_session_master_7", "ach_desc_session_master_7", self._check_session_master,
             250),
            ("polyglot_1", "🌍", "ach_polyglot_1", "ach_desc_polyglot_1", self._check_polyglot, 2),
            ("polyglot_2", "🌍", "ach_polyglot_2", "ach_desc_polyglot_2", self._check_polyglot, 3),
            ("polyglot_3", "🌍", "ach_polyglot_3", "ach_desc_polyglot_3", self._check_polyglot, 5),
            ("polyglot_4", "🌍", "ach_polyglot_4", "ach_desc_polyglot_4", self._check_polyglot, 10),
            ("polyglot_5", "🌍", "ach_polyglot_5", "ach_desc_polyglot_5", self._check_polyglot, 20),
            ("polyglot_6", "🌍", "ach_polyglot_6", "ach_desc_polyglot_6", self._check_polyglot, 50),
            ("polyglot_7", "🌍", "ach_polyglot_7", "ach_desc_polyglot_7", self._check_polyglot, 100),
            ("polyglot_8", "🌍", "ach_polyglot_8", "ach_desc_polyglot_8", self._check_polyglot, 500),
            ("strategist_1", "📅", "ach_strategist_1", "ach_desc_strategist_1", self._check_strategist, 7),
            ("strategist_2", "📅", "ach_strategist_2", "ach_desc_strategist_2", self._check_strategist, 14),
            ("strategist_3", "📅", "ach_strategist_3", "ach_desc_strategist_3", self._check_strategist, 30),
            ("strategist_4", "📅", "ach_strategist_4", "ach_desc_strategist_4", self._check_strategist, 60),
        ]

    def check_all(self, silent=False):
        new_unlocks = []
        for ach_id, icon, title_key, desc_key, check_func, threshold in self.definitions:
            if ach_id in self.data["achievements"]:
                continue

            is_unlocked = check_func(threshold) if threshold is not None else check_func()

            if is_unlocked:
                self.data["achievements"].append(ach_id)
                new_unlocks.append((icon, title_key, desc_key))

        if new_unlocks:
            save(self.data)
            if not silent:
                self.notification_queue.extend(new_unlocks)
                self.process_queue()

    def process_queue(self):
        if self.is_showing_popup or not self.notification_queue:
            return

        self.is_showing_popup = True
        icon, title_key, desc_key = self.notification_queue.pop(0)
        UnlockPopup(self.parent, self.txt, icon, title_key, desc_key, on_close=self.on_popup_closed)

    def on_popup_closed(self):
        self.is_showing_popup = False
        self.parent.after(200, self.process_queue)

    def get_current_metric(self, check_func):
        if check_func == self._check_first_step:
            return self.data["global_stats"].get("topics_done", 0)
        elif check_func == self._check_balance:
            return self.data["global_stats"].get("days_off", 0)
        elif check_func == self._check_scribe:
            return self.data["global_stats"].get("notes_added", 0)
        elif check_func == self._check_encyclopedia:
            return self.data["global_stats"].get("topics_done", 0)
        elif check_func == self._check_time_lord:
            return self.data["global_stats"].get("pomodoro_sessions", 0)
        elif check_func == self._check_polyglot:
            return self.data["global_stats"].get("exams_added", 0)
        elif check_func == self._check_session_master:
            return self._get_session_master_count()
        elif check_func == self._check_strategist:
            return self._get_max_strategy_days()
        else:
            return 0

    def _check_first_step(self, threshold):
        return self.data["global_stats"].get("topics_done", 0) >= threshold

    def _check_clean_sheet(self):
        today = date.today()
        from core.planner import date_format
        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= today}
        overdue_count = 0
        for t in self.data["topics"]:
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < today:
                if t["status"] == "todo" and t["exam_id"] in active_exams_ids:
                    overdue_count += 1

        had_overdue = self.data["global_stats"].get("had_overdue", False)
        if overdue_count > 0:
            if not had_overdue:
                self.data["global_stats"]["had_overdue"] = True
                save(self.data)
            return False
        else:
            return had_overdue

    def _check_balance(self, threshold):
        return self.data["global_stats"].get("days_off", 0) >= threshold

    def _check_scribe(self, threshold):
        return self.data["global_stats"].get("notes_added", 0) >= threshold

    def _check_encyclopedia(self, threshold):
        return self.data["global_stats"].get("topics_done", 0) >= threshold

    def _check_time_lord(self, threshold):
        return self.data["global_stats"].get("pomodoro_sessions", 0) >= threshold

    def _check_polyglot(self, threshold):
        return self.data["global_stats"].get("exams_added", 0) >= threshold

    def _get_session_master_count(self):
        exam_counts = {}
        for t in self.data["topics"]:
            eid = t["exam_id"]
            if eid not in exam_counts: exam_counts[eid] = [0, 0]
            exam_counts[eid][0] += 1
            if t["status"] == "done": exam_counts[eid][1] += 1
        completed = 0
        for eid, counts in exam_counts.items():
            if counts[0] >= 3 and counts[0] == counts[1]: completed += 1
        return completed

    def _check_session_master(self, threshold):
        return self._get_session_master_count() >= threshold

    def _get_max_strategy_days(self):
        today = date.today()
        from core.planner import date_format
        max_days = 0
        for e in self.data["exams"]:
            diff = (date_format(e["date"]) - today).days
            if diff > max_days: max_days = diff
        return max_days

    def _check_strategist(self, threshold):
        return self._get_max_strategy_days() >= threshold


class UnlockPopup:
    def __init__(self, parent, txt, icon, title_key, desc_key, on_close=None):
        self.on_close_callback = on_close
        self.win = ctk.CTkToplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)

        width = 400
        height = 300
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2)
        self.win.geometry(f"{width}x{height}+{x}+{y}")

        self.alpha = 0.0
        self.win.attributes("-alpha", self.alpha)

        mode = ctk.get_appearance_mode()
        bg_color = "#f0f0f0" if mode == "Light" else "#222222"
        desc_color = "#333333" if mode == "Light" else "#ecf0f1"
        self.colors = ['#f1c40f', '#e67e22', '#e74c3c', '#2ecc71', '#3498db', '#9b59b6']

        self.canvas = tk.Canvas(self.win, bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        title_txt = txt.get(title_key, title_key)
        desc_txt = txt.get(desc_key, desc_key)

        # --- ZMIANA: Usunięcie zabetonowanego tekstu powiadomienia ---
        popup_header = txt.get("ach_unlocked_popup_title", "✨ UNLOCKED! ✨")

        self.canvas.create_text(width / 2, 40, text=popup_header, font=("Arial", 14, "bold"), fill="#f39c12")
        self.canvas.create_text(width / 2, 110, text=icon, font=("Arial", 80), fill=desc_color)
        self.canvas.create_text(width / 2, 180, text=title_txt, font=("Arial", 22, "bold"), fill="#2ecc71")
        self.canvas.create_text(width / 2, 230, text=desc_txt, font=("Arial", 12), fill=desc_color, width=350,
                                justify="center")

        self.particles = []
        self.running = True
        for _ in range(6):
            start_x = random.randint(50, width - 50)
            start_y = random.randint(50, height // 2)
            for _ in range(70):
                self.particles.append(Particle(self.canvas, start_x, start_y, self.colors))

        self.win.bell()
        self.fade_in()
        self.animate_fireworks()
        self.canvas.bind("<Button-1>", self.immediate_close)

    def animate_fireworks(self):
        if not self.running: return
        alive = []
        for p in self.particles:
            p.update()
            if p.is_alive():
                alive.append(p)
            else:
                self.canvas.delete(p.id)
        self.particles = alive
        if self.particles: self.win.after(20, self.animate_fireworks)

    def fade_in(self):
        if self.alpha < 1.0:
            self.alpha += 0.05
            self.win.attributes("-alpha", self.alpha)
            self.win.after(20, self.fade_in)
        else:
            self.win.after(4000, self.start_fade_out)

    def start_fade_out(self):
        self.running = False
        self.fade_out()

    def fade_out(self):
        if self.alpha > 0.0:
            self.alpha -= 0.05
            self.win.attributes("-alpha", self.alpha)
            self.win.after(20, self.fade_out)
        else:
            self.win.destroy()
            if self.on_close_callback:
                self.on_close_callback()

    def immediate_close(self, event=None):
        self.start_fade_out()


class StaticAchievementItem(ctk.CTkFrame):
    def __init__(self, parent, icon, title, desc, is_unlocked, *args, **kwargs):
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


class AccordionItem(ctk.CTkFrame):
    # --- DODANO: Argument 'txt' do konstruktora ---
    def __init__(self, parent, txt, icon, title, level_text, details_list, is_unlocked, *args, **kwargs):
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

        # --- ZMIANA: Pobranie hintu ze słownika ---
        lbl_hint = ctk.CTkLabel(info_frame, text=self.txt.get("ach_click_to_expand", "Click to expand"),
                                font=("Arial", 10), text_color="gray", anchor="w")
        lbl_hint.pack(fill="x")

        for w in [lbl_icon, info_frame, lbl_title, lbl_hint, self.content_frame]:
            w.bind("<Button-1>", lambda e: self.toggle())

        self.details_frame = ctk.CTkFrame(self, fg_color="transparent")

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


class AchievementsWindow:
    def __init__(self, parent, txt, data, btn_style):
        self.txt = txt
        self.data = data
        self.manager = AchievementManager(parent, txt, data)
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_achievements", "Achievements"))
        self.win.geometry("500x650")
        self.win.resizable(False, True)

        # --- ZMIANA: Nagłówek okna pobrany ze słownika ---
        header_text = self.txt.get("ach_win_header_label", "🏆 Your Achievements")
        ctk.CTkLabel(self.win, text=header_text, font=("Arial", 20, "bold")).pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self.win, width=460, height=500)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.build_list()

        ctk.CTkButton(self.win, text=self.txt["btn_close"], command=self.win.destroy,
                      fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90")
                      ).pack(pady=10)

    def build_list(self):
        unlocked_ids = self.data.get("achievements", [])
        families = {}
        order = ["first_step", "clean_sheet", "balance", "scribe", "encyclopedia", "time_lord", "session_master",
                 "polyglot", "strategist"]
        family_meta = {}

        for ach_id, icon, title_key, desc_key, check_func, threshold in self.manager.definitions:
            parts = ach_id.rsplit('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                base = parts[0]
                lvl = int(parts[1])
            else:
                base = ach_id
                lvl = 0

            if base not in families: families[base] = []

            t_text = self.txt.get(title_key, title_key)
            d_text = self.txt.get(desc_key, desc_key)

            is_unlocked = ach_id in unlocked_ids

            if not is_unlocked and threshold is not None:
                current_val = self.manager.get_current_metric(check_func)
                d_text += f" ({current_val}/{threshold})"

            families[base].append({
                "id": ach_id, "lvl": lvl, "title": t_text, "desc": d_text,
                "unlocked": is_unlocked
            })
            if base not in family_meta:
                clean_title = t_text.split(" I")[0].split(" IV")[0].strip()
                family_meta[base] = {"icon": icon, "title": clean_title}

        for base in order:
            if base not in families: continue
            items = sorted(families[base], key=lambda x: x["lvl"])
            meta = family_meta[base]

            if len(items) == 1 and items[0]["lvl"] == 0:
                item = items[0]
                StaticAchievementItem(
                    self.scroll_frame,
                    icon=meta["icon"],
                    title=item["title"],
                    desc=item["desc"],
                    is_unlocked=item["unlocked"]
                ).pack(fill="x", pady=5)
            else:
                highest_lvl_idx = -1
                for i, it in enumerate(items):
                    if it["unlocked"]: highest_lvl_idx = i

                is_unlocked_any = highest_lvl_idx >= 0

                display_title = items[highest_lvl_idx]["title"] if is_unlocked_any else meta["title"]
                level_suffix = ""

                details = []
                for it in items:
                    details.append((it["title"], it["desc"], it["unlocked"]))

                # --- ZMIANA: Przekazanie self.txt do AccordionItem ---
                AccordionItem(
                    self.scroll_frame,
                    self.txt,
                    icon=meta["icon"],
                    title=display_title,
                    level_text=level_suffix,
                    details_list=details,
                    is_unlocked=is_unlocked_any
                ).pack(fill="x", pady=5)