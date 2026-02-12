import tkinter as tk
import customtkinter as ctk
import random
import math as import_math
import math


# --- KLASA BAZOWA ---
class BaseFadingEffect:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.window = None
        self.canvas = None
        self.is_running = False
        self.particles = []
        self.generation_steps = 0
        self.alpha = 0.0

    def _get_parent_color(self):
        """Pobiera rzeczywisty kolor tła z rodzica (CustomTkinter)"""
        try:
            # ctk zwraca tuple (kolor_jasny, kolor_ciemny) lub pojedynczy string
            fg = self.parent.cget("fg_color")

            if isinstance(fg, (list, tuple)):
                mode = ctk.get_appearance_mode()
                return fg[1] if mode == "Dark" else fg[0]
            return fg
        except:
            return "#242424"  # Fallback

    def _get_text_color(self, bg_color):
        if str(bg_color).lower().startswith(("#2", "#3", "#0", "#1")):
            return "#ffffff"
        return "#333333"

    def _create_window(self):
        if self.window is not None:
            try:
                self.window.destroy()
            except:
                pass

        bg_color = self._get_parent_color()
        self.text_color = self._get_text_color(bg_color)

        self.window = tk.Toplevel(self.parent)
        self.window.overrideredirect(True)
        self.window.configure(bg=bg_color)
        self.window.attributes("-alpha", 0.0)
        self.alpha = 0.0

        # Wymuszamy odświeżenie geometrii
        self.parent.winfo_toplevel().update_idletasks()

        x = self.parent.winfo_rootx()
        y = self.parent.winfo_rooty()
        w = self.parent.winfo_width()
        h = self.parent.winfo_height()

        # Geometria 1:1
        self.window.geometry(f"{w}x{h}+{x}+{y}")

        self.window.transient(self.parent.winfo_toplevel())
        self.window.lift()

        # --- NOWOŚĆ: Kliknięcie w okno wyłącza animację ---
        # Używamy lambda, żeby zignorować argument 'event', który wysyła tkinter
        self.window.bind("<Button-1>", lambda e: self.start_fade_out())

        # Płótno z wymuszonym brakiem krawędzi
        self.canvas = tk.Canvas(self.window, bg=bg_color, highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        # --- NOWOŚĆ: Kliknięcie w płótno (i elementy na nim) też wyłącza ---
        self.canvas.bind("<Button-1>", lambda e: self.start_fade_out())

        return w, h

    def fade_in(self):
        if not self.window: return
        if self.alpha < 1.0:
            self.alpha += 0.1
            if self.alpha > 1.0: self.alpha = 1.0
            self.window.attributes("-alpha", self.alpha)
            self.window.after(30, self.fade_in)

    def start_fade_out(self):
        # Ta funkcja rozpoczyna proces znikania
        # Ustawiamy is_running na False, żeby przestać generować nowe cząsteczki
        self.is_running = False
        self._fade_out_step()

    def _fade_out_step(self):
        if not self.window: return
        if self.alpha > 0.0:
            self.alpha -= 0.08  # Zwiększyłem lekko prędkość znikania przy kliknięciu (0.05 -> 0.08)
            if self.alpha < 0.0: self.alpha = 0.0
            self.window.attributes("-alpha", self.alpha)
            self.window.after(30, self._fade_out_step)
        else:
            self.stop()

    def stop(self):
        self.is_running = False
        if self.window:
            self.window.destroy()
            self.window = None


# --- EFEKT 1: KONFETTI ---
class ConfettiEffect(BaseFadingEffect):
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.colors = ["#f1c40f", "#2ecc71", "#3498db", "#e74c3c", "#9b59b6", "#e67e22", "#1abc9c"]

    def start(self, text="Dobra robota!"):
        w, h = self._create_window()
        self.fade_in()

        self.canvas.create_text(w / 2, h / 3, text=text, fill=self.text_color,
                                font=("Arial", 16, "bold"), justify="center", width=w - 20)

        self.particles = []
        self.is_running = True
        self.generation_steps = 80
        self.animate()

    def spawn_batch(self, count=2):
        if not self.window: return
        w = self.window.winfo_width()
        for _ in range(count):
            x = random.randint(0, w)
            y = random.randint(-20, 0)
            vx = random.uniform(-2, 2)
            vy = random.uniform(2, 5)
            size = random.randint(3, 7)
            color = random.choice(self.colors)
            item = self.canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")
            self.particles.append({"id": item, "vx": vx, "vy": vy, "x": x, "y": y})

    def animate(self):
        if not self.window or not self.window.winfo_exists(): return

        if self.is_running and self.generation_steps > 0:
            self.spawn_batch(count=3)
            self.generation_steps -= 1

        particles_left = False
        h = self.window.winfo_height()

        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.98
            self.canvas.coords(p["id"], p["x"], p["y"], p["x"] + 6, p["y"] + 6)
            if p["y"] < h + 20: particles_left = True

        if (self.is_running and self.generation_steps > 0) or particles_left:
            self.window.after(20, self.animate)
        else:
            self.start_fade_out()


# --- EFEKT 2: FAJERWERKI ---
class FireworksEffect(BaseFadingEffect):
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.colors = ["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff", "#ffffff"]

    def start(self, text="Gratulacje!"):
        w, h = self._create_window()
        self.fade_in()

        self.canvas.create_text(w / 2, h / 3, text=text, fill=self.text_color,
                                font=("Arial", 16, "bold"), justify="center", width=w - 20)

        self.particles = []
        self.is_running = True
        self.generation_steps = 15
        self.animate()

    def spawn_explosion(self):
        if not self.window: return
        w = self.window.winfo_width()
        h = self.window.winfo_height()

        cx = random.randint(20, w - 20)
        cy = random.randint(20, int(h / 2) + 50)
        color = random.choice(self.colors)

        for _ in range(20):
            angle = random.uniform(0, 6.28)
            speed = random.uniform(2, 6)
            vx = import_math.cos(angle) * speed
            vy = import_math.sin(angle) * speed
            size = random.randint(2, 4)
            item = self.canvas.create_oval(cx, cy, cx + size, cy + size, fill=color, outline="")
            self.particles.append({"id": item, "x": cx, "y": cy, "vx": vx, "vy": vy, "life": random.randint(20, 40)})

    def animate(self):
        if not self.window or not self.window.winfo_exists(): return

        if self.is_running and self.generation_steps > 0 and random.random() < 0.15:
            self.spawn_explosion()
            self.generation_steps -= 1

        particles_left = False
        for i in range(len(self.particles) - 1, -1, -1):
            p = self.particles[i]
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.2
            p["vx"] *= 0.95
            p["life"] -= 1
            self.canvas.coords(p["id"], p["x"], p["y"], p["x"] + 4, p["y"] + 4)
            if p["life"] > 0:
                particles_left = True
            else:
                self.canvas.delete(p["id"])
                self.particles.pop(i)

        if (self.is_running and self.generation_steps > 0) or particles_left:
            self.window.after(30, self.animate)
        else:
            self.start_fade_out()


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