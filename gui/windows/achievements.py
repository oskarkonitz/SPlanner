import customtkinter as ctk
import tkinter as tk
from datetime import date
from core.planner import date_format
from core.storage import save
import random
import math


# --- KLASA POMOCNICZA DLA FAJERWERKÓW ---
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
        if self.life < 20:
            self.size *= 0.9

    def is_alive(self):
        return self.life > 0


# --- KLASA MANAGERA (LOGIKA WIELOPOZIOMOWA) ---
class AchievementManager:
    def __init__(self, parent_window, txt, data):
        self.parent = parent_window
        self.txt = txt
        self.data = data
        if "achievements" not in self.data:
            self.data["achievements"] = []

        # Definicje osiągnięć z poziomami (lambda pozwala przekazać parametry do funkcji)
        self.definitions = [
            # POJEDYNCZE
            ("first_step", "👶", "ach_first_step", "ach_desc_first_step", self._check_first_step),
            ("clean_sheet", "🧹", "ach_clean_sheet", "ach_desc_clean_sheet", self._check_clean_sheet),
            ("balance", "🏖️", "ach_balance", "ach_desc_balance", self._check_balance),

            # SKRYBA (Notatki): 5, 10, 25, 50, 100
            ("scribe_1", "✍", "ach_scribe_1", "ach_desc_scribe_1", lambda: self._check_scribe(5)),
            ("scribe_2", "✍", "ach_scribe_2", "ach_desc_scribe_2", lambda: self._check_scribe(10)),
            ("scribe_3", "✍", "ach_scribe_3", "ach_desc_scribe_3", lambda: self._check_scribe(25)),
            ("scribe_4", "✍", "ach_scribe_4", "ach_desc_scribe_4", lambda: self._check_scribe(50)),
            ("scribe_5", "✍", "ach_scribe_5", "ach_desc_scribe_5", lambda: self._check_scribe(100)),

            # ENCYKLOPEDIA (Tematy): 10, 25, 50, 100, 200
            ("encyclopedia_1", "📚", "ach_encyclopedia_1", "ach_desc_encyclopedia_1",
             lambda: self._check_encyclopedia(10)),
            ("encyclopedia_2", "📚", "ach_encyclopedia_2", "ach_desc_encyclopedia_2",
             lambda: self._check_encyclopedia(25)),
            ("encyclopedia_3", "📚", "ach_encyclopedia_3", "ach_desc_encyclopedia_3",
             lambda: self._check_encyclopedia(50)),
            ("encyclopedia_4", "📚", "ach_encyclopedia_4", "ach_desc_encyclopedia_4",
             lambda: self._check_encyclopedia(100)),
            ("encyclopedia_5", "📚", "ach_encyclopedia_5", "ach_desc_encyclopedia_5",
             lambda: self._check_encyclopedia(200)),

            # WŁADCA CZASU (Pomodoro): 5, 10, 25, 50, 100
            ("time_lord_1", "🍅", "ach_time_lord_1", "ach_desc_time_lord_1", lambda: self._check_time_lord(5)),
            ("time_lord_2", "🍅", "ach_time_lord_2", "ach_desc_time_lord_2", lambda: self._check_time_lord(10)),
            ("time_lord_3", "🍅", "ach_time_lord_3", "ach_desc_time_lord_3", lambda: self._check_time_lord(25)),
            ("time_lord_4", "🍅", "ach_time_lord_4", "ach_desc_time_lord_4", lambda: self._check_time_lord(50)),
            ("time_lord_5", "🍅", "ach_time_lord_5", "ach_desc_time_lord_5", lambda: self._check_time_lord(100)),

            # MISTRZ SESJI (Ukończone w 100% egzaminy): 1, 3, 5
            ("session_master_1", "🎓", "ach_session_master_1", "ach_desc_session_master_1",
             lambda: self._check_session_master(1)),
            ("session_master_2", "🎓", "ach_session_master_2", "ach_desc_session_master_2",
             lambda: self._check_session_master(3)),
            ("session_master_3", "🎓", "ach_session_master_3", "ach_desc_session_master_3",
             lambda: self._check_session_master(5)),

            # POLIGLOTA (Różne przedmioty): 2, 3, 5
            ("polyglot_1", "🌍", "ach_polyglot_1", "ach_desc_polyglot_1", lambda: self._check_polyglot(2)),
            ("polyglot_2", "🌍", "ach_polyglot_2", "ach_desc_polyglot_2", lambda: self._check_polyglot(3)),
            ("polyglot_3", "🌍", "ach_polyglot_3", "ach_desc_polyglot_3", lambda: self._check_polyglot(5)),

            # STRATEG (Dni wyprzedzenia): 7, 14, 30
            ("strategist_1", "📅", "ach_strategist_1", "ach_desc_strategist_1", lambda: self._check_strategist(7)),
            ("strategist_2", "📅", "ach_strategist_2", "ach_desc_strategist_2", lambda: self._check_strategist(14)),
            ("strategist_3", "📅", "ach_strategist_3", "ach_desc_strategist_3", lambda: self._check_strategist(30)),
        ]

    def check_all(self, silent=False):
        new_unlocks = []
        for ach_id, icon, title_key, desc_key, check_func in self.definitions:
            # Kluczowe: jeśli ID już jest w bazie, pomijamy -> animacja tylko raz!
            if ach_id in self.data["achievements"]:
                continue

            if check_func():
                self.data["achievements"].append(ach_id)
                new_unlocks.append((icon, title_key, desc_key))

        if new_unlocks:
            save(self.data)
            if not silent:
                # Wyświetlamy wszystkie nowe (układając kaskadowo/stosując pętlę)
                # Dzięki temu jak odblokujesz 3 naraz, zobaczysz 3 okienka
                for icon, t_key, d_key in new_unlocks:
                    self.show_unlock_popup(icon, t_key, d_key)

    def show_unlock_popup(self, icon, title_key, desc_key):
        UnlockPopup(self.parent, self.txt, icon, title_key, desc_key)

    # --- WARUNKI SPARAMETRYZOWANE ---
    def _check_first_step(self):
        return any(t["status"] == "done" for t in self.data["topics"])

    def _check_clean_sheet(self):
        if not self.data["topics"]: return False
        today = date.today()
        active_exams_ids = {e["id"] for e in self.data["exams"] if date_format(e["date"]) >= today}
        overdue_count = 0
        for t in self.data["topics"]:
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < today:
                if t["status"] == "todo" and t["exam_id"] in active_exams_ids:
                    overdue_count += 1
        return overdue_count == 0

    def _check_balance(self):
        return len(self.data.get("blocked_dates", [])) > 0

    # Funkcje przyjmują teraz argument 'threshold' (wymagana ilość)
    def _check_scribe(self, threshold):
        notes_count = sum(1 for t in self.data["topics"] if t.get("note", "").strip())
        notes_count += sum(1 for e in self.data["exams"] if e.get("note", "").strip())
        return notes_count >= threshold

    def _check_encyclopedia(self, threshold):
        done_count = sum(1 for t in self.data["topics"] if t["status"] == "done")
        return done_count >= threshold

    def _check_time_lord(self, threshold):
        return self.data.get("stats", {}).get("pomodoro_count", 0) >= threshold

    def _check_session_master(self, threshold):
        # Liczy ile egzaminów jest zrobionych w 100%
        exam_counts = {}
        for t in self.data["topics"]:
            eid = t["exam_id"]
            if eid not in exam_counts: exam_counts[eid] = [0, 0]
            exam_counts[eid][0] += 1
            if t["status"] == "done": exam_counts[eid][1] += 1

        completed_exams = 0
        for eid, counts in exam_counts.items():
            # Musi mieć min. 3 tematy, żeby zaliczyć jako "egzamin" do statystyk
            if counts[0] >= 3 and counts[0] == counts[1]:
                completed_exams += 1
        return completed_exams >= threshold

    def _check_polyglot(self, threshold):
        subjects = {e["subject"].lower().strip() for e in self.data["exams"]}
        return len(subjects) >= threshold

    def _check_strategist(self, threshold):
        today = date.today()
        for e in self.data["exams"]:
            if (date_format(e["date"]) - today).days >= threshold: return True
        return False


# --- NOWE OKNO GRATULACJI (BEZ ZMIAN WZGLĘDEM POPRZEDNIEJ WERSJI) ---
class UnlockPopup:
    def __init__(self, parent, txt, icon, title_key, desc_key):
        self.win = ctk.CTkToplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)

        width = 400
        height = 300
        # Dodajemy mały losowy offset, żeby przy odblokowaniu kilku naraz okna się nie pokryły idealnie
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-20, 20)

        x = parent.winfo_x() + (parent.winfo_width() // 2) - (width // 2) + offset_x
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (height // 2) + offset_y
        self.win.geometry(f"{width}x{height}+{x}+{y}")

        self.alpha = 0.0
        self.win.attributes("-alpha", self.alpha)

        mode = ctk.get_appearance_mode()
        if mode == "Light":
            bg_color = "#f0f0f0"
            desc_color = "#333333"
            self.colors = ['#f1c40f', '#e67e22', '#e74c3c', '#2ecc71', '#3498db', '#9b59b6', '#333333']
        else:
            bg_color = "#222222"
            desc_color = "#ecf0f1"
            self.colors = ['#f1c40f', '#e67e22', '#e74c3c', '#2ecc71', '#3498db', '#9b59b6', '#ffffff']

        self.canvas = tk.Canvas(self.win, bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        title_txt = txt.get(title_key, title_key)
        desc_txt = txt.get(desc_key, desc_key)
        header_txt = "✨ ODBLOKOWANO OSIĄGNIĘCIE! ✨"

        self.canvas.create_text(width / 2, 40, text=header_txt, font=("Arial", 14, "bold"), fill="#f39c12")
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
        alive_particles = []
        for p in self.particles:
            p.update()
            if p.is_alive():
                alive_particles.append(p)
            else:
                self.canvas.delete(p.id)
        self.particles = alive_particles
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

    def immediate_close(self, event=None):
        self.start_fade_out()


# --- OKNO LISTY OSIĄGNIĘĆ (BEZ ZMIAN) ---
class AchievementsWindow:
    def __init__(self, parent, txt, data, btn_style):
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.manager = AchievementManager(parent, txt, data)
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_achievements", "Osiągnięcia"))
        self.win.geometry("500x600")
        self.win.resizable(False, True)
        ctk.CTkLabel(self.win, text="🏆 " + self.txt.get("achievements_header", "Twoje Osiągnięcia"),
                     font=("Arial", 20, "bold")).pack(pady=15)
        self.scroll_frame = ctk.CTkScrollableFrame(self.win, width=460, height=500)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.build_list()
        ctk.CTkButton(self.win, text=self.txt["btn_close"], command=self.win.destroy,
                      fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90")
                      ).pack(pady=10)

    def build_list(self):
        unlocked_ids = self.data.get("achievements", [])
        for ach_id, icon, title_key, desc_key, _ in self.manager.definitions:
            is_unlocked = ach_id in unlocked_ids
            bg_color = ("gray90", "gray20") if is_unlocked else ("gray95", "gray15")
            icon_display = icon if is_unlocked else "🔒"
            title_text = self.txt.get(title_key, title_key)
            desc_text = self.txt.get(desc_key, desc_key)
            status_color = "#27ae60" if is_unlocked else "gray"
            card = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, corner_radius=10)
            card.pack(fill="x", pady=5, padx=5)
            lbl_icon = ctk.CTkLabel(card, text=icon_display, font=("Arial", 30))
            lbl_icon.grid(row=0, column=0, rowspan=2, padx=15, pady=10)
            lbl_title = ctk.CTkLabel(card, text=title_text, font=("Arial", 14, "bold"),
                                     text_color=status_color, anchor="w")
            lbl_title.grid(row=0, column=1, sticky="w", padx=(0, 10), pady=(10, 0))
            lbl_desc = ctk.CTkLabel(card, text=desc_text, font=("Arial", 12),
                                    text_color=("gray40", "gray60"), anchor="w", wraplength=350)
            lbl_desc.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=(0, 10))
            card.columnconfigure(1, weight=1)