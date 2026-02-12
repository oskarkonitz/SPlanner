import customtkinter as ctk
import tkinter as tk
import random
from gui.effects import Particle

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