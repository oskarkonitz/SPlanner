from PIL import Image
import os


def create_icons(input_filename="source_icon.png"):
    # Sprawdzamy czy plik źródłowy istnieje
    if not os.path.exists(input_filename):
        print(f"BŁĄD: Nie znaleziono pliku '{input_filename}'!")
        return

    try:
        img = Image.open(input_filename).convert("RGBA")

        # --- 1. Generowanie .icns (dla macOS) ---
        print("Generowanie icon.icns (Mac)...")
        if img.size != (1024, 1024):
            img_mac = img.resize((1024, 1024), Image.Resampling.LANCZOS)
        else:
            img_mac = img
        img_mac.save("icon.icns", format="ICNS")

        # --- 2. Generowanie .ico (dla Windows) ---
        print("Generowanie icon.ico (Windows)...")
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save("icon.ico", format="ICO", sizes=icon_sizes)

        # --- 3. Generowanie .png (dla Linuxa) ---
        print("Generowanie icon.png (Linux)...")
        # Standardowa duża ikona Linuxa to zazwyczaj 512x512
        img_linux = img.resize((512, 512), Image.Resampling.LANCZOS)
        img_linux.save("icon.png", format="PNG")

        print("\n✅ SUKCES! Utworzono: icon.icns, icon.ico, icon.png")
        print("👉 Pamiętaj, aby przenieść te pliki do folderu 'assets'!")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")


if __name__ == "__main__":
    create_icons()