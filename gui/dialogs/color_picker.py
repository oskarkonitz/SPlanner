import customtkinter as ctk
import tkinter as tk
import colorsys


class ColorPickerWindow(ctk.CTkToplevel):
    def __init__(self, parent, txt, current_color, callback):
        super().__init__(parent)
        self.callback = callback
        self.txt = txt
        self.title(self.txt.get("win_color_picker", "Select Color"))
        self.geometry("350x450")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Ustawienie modale (blokuje okno rodzica)
        self.transient(parent)
        self.grab_set()

        # Domyślne wartości HSV
        self.hue = 0.0
        self.sat = 1.0
        self.val = 1.0
        self.selected_color = current_color

        # --- PODGLĄD KOLORU ---
        self.preview_frame = ctk.CTkFrame(self, height=50, corner_radius=10, fg_color=current_color)
        self.preview_frame.pack(fill="x", padx=20, pady=(20, 10))

        # --- PŁÓTNO GŁÓWNE (Saturacja/Jasność) ---
        # Rysujemy to raz i używamy tagów do zmiany kolorów, żeby było szybciej
        self.canvas_sv = tk.Canvas(self, height=200, width=300, highlightthickness=0, bg="#2b2b2b")
        self.canvas_sv.pack(pady=10)
        self.canvas_sv.bind("<Button-1>", self.on_sv_click)
        self.canvas_sv.bind("<B1-Motion>", self.on_sv_click)

        # --- PASEK ODCIENI (HUE) ---
        self.canvas_hue = tk.Canvas(self, height=30, width=300, highlightthickness=0)
        self.canvas_hue.pack(pady=10)
        self.canvas_hue.bind("<Button-1>", self.on_hue_click)
        self.canvas_hue.bind("<B1-Motion>", self.on_hue_click)

        # Generowanie UI
        self.draw_hue_bar()
        self.draw_sv_box()

        # --- PRZYCISKI ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text=self.txt.get("btn_select", "Select"), command=self.confirm).pack(side="left",
                                                                                                       padx=10)
        ctk.CTkButton(btn_frame, text=self.txt.get("btn_cancel", "Cancel"), command=self.destroy,
                      fg_color="transparent", border_width=1).pack(side="left", padx=10)

    def draw_hue_bar(self):
        # Rysuje tęczowy pasek
        for i in range(300):
            rgb = colorsys.hsv_to_rgb(i / 300.0, 1.0, 1.0)
            color = "#%02x%02x%02x" % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            self.canvas_hue.create_line(i, 0, i, 30, fill=color)

    def draw_sv_box(self):
        # Rysuje gradient Saturacji (X) i Wartości (Y) dla aktualnego Hue
        # Rysujemy pionowe linie zmieniające nasycenie, a na nich "cień" jasności
        # Uwaga: Pełne rysowanie pixel-by-pixel w pythonie jest wolne.
        # Używamy uproszczenia: tło to kolor HUE, na to nakładamy biały gradient (poziomo) i czarny (pionowo)

        self.canvas_sv.delete("all")

        # Baza (Hue)
        rgb = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
        base_color = "#%02x%02x%02x" % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        self.canvas_sv.configure(bg=base_color)

        # Nakładka bieli (Saturacja - od lewej do prawej)
        # Tkinter nie ma alpha-gradientów wprost, więc symulujemy prostokątami
        # Dla wydajności lepiej zrobić prosty wybór z predefiniowanych palet,
        # ale tutaj zrobimy "Siatkę" kolorów.

        # WERSJA UPROSZCZONA DLA WYDAJNOŚCI:
        # Rysujemy siatkę 30x20 prostokątów (10x10 px każdy)
        step_x = 300 / 30
        step_y = 200 / 20

        for y in range(20):
            val = 1.0 - (y / 20.0)  # Jasność maleje w dół
            for x in range(30):
                sat = x / 30.0  # Saturacja rośnie w prawo

                rgb = colorsys.hsv_to_rgb(self.hue, sat, val)
                color = "#%02x%02x%02x" % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                self.canvas_sv.create_rectangle(x * step_x, y * step_y, (x + 1) * step_x, (y + 1) * step_y, fill=color,
                                                outline=color)

    def on_hue_click(self, event):
        x = max(0, min(event.x, 299))
        self.hue = x / 300.0
        self.draw_sv_box()
        self.update_preview()

    def on_sv_click(self, event):
        x = max(0, min(event.x, 299))
        y = max(0, min(event.y, 199))

        self.sat = x / 300.0
        self.val = 1.0 - (y / 200.0)
        self.update_preview()

    def update_preview(self):
        rgb = colorsys.hsv_to_rgb(self.hue, self.sat, self.val)
        self.selected_color = "#%02x%02x%02x" % (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        self.preview_frame.configure(fg_color=self.selected_color)

    def confirm(self):
        self.callback(self.selected_color)
        self.destroy()