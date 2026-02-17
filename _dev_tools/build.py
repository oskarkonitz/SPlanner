import PyInstaller.__main__
import platform
import os
import shutil


def build_app():



    # 1. Ustalanie ścieżek
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(script_dir, "assets")
    main_script_path = os.path.join(project_root, "main.py")

    # --- KONFIGURACJA FOLDERU WYJŚCIOWEGO ---
    output_folder_name = "planner_build"
    base_output_dir = os.path.join(project_root, output_folder_name)

    dist_dir = os.path.join(base_output_dir, "dist")
    work_dir = os.path.join(base_output_dir, "temp")

    # CZYSZCZENIE: Jeśli folder planner_build już istnieje, usuń go
    if os.path.exists(base_output_dir):
        print(f" Czyszczenie starego folderu: {base_output_dir}...")
        try:
            shutil.rmtree(base_output_dir)  # Do tego potrzebny jest ten import!
        except Exception as e:
            print(f" Nie udało się usunąć folderu (może jest otwarty?): {e}")

    if not os.path.exists(base_output_dir):
        os.makedirs(base_output_dir)
        print(f" Utworzono folder na buildy: {base_output_dir}")

    # 2. Wykrywanie systemu
    system_os = platform.system()
    print(f" Wykryto system: {system_os}")

    # --- LOGIKA SYSTEMÓW ---
    if system_os == "Darwin":  # macOS
        icon_path = os.path.join(assets_dir, "icon.icns")
        separator = ":"
    elif system_os == "Windows":
        icon_path = os.path.join(assets_dir, "icon.ico")
        separator = ";"
    elif system_os == "Linux":  # Linux
        icon_path = os.path.join(assets_dir, "icon.png")  # Linux używa PNG
        separator = ":"  # Linux używa dwukropka jak Mac
    else:
        icon_path = None
        separator = ":"

    # Sprawdzenie ikony
    if icon_path and not os.path.exists(icon_path):
        print(f" Nie znaleziono ikony: {icon_path}. Używam domyślnej.")
        icon_path = None

    # 3. Konfiguracja PyInstaller
    print(f" Konfiguracja budowania dla {system_os}...")

    # Opcje wspólne dla obu systemów
    opts = [
        main_script_path,
        '--name=Splanner',
        '--windowed',
        '--noconsole',
        f'--add-data={os.path.join(project_root, "languages")}{separator}languages',
        f'--add-data={os.path.join(script_dir, "source_icon.png")}{separator}_dev_tools',
        '--clean',
        f'--distpath={dist_dir}',
        f'--workpath={work_dir}',
        f'--specpath={base_output_dir}'
    ]

    # --- LOGIKA SPECYFICZNA DLA SYSTEMU ---
    if system_os == "Windows":
        # Windows: Chcemy jeden plik .exe (łatwiejsze pobieranie, naprawia błąd GitHub Actions)
        opts.append('--onefile')
    else:
        # macOS: Chcemy .app (onedir), bo --onefile psuje działanie GUI na Macu
        opts.append('--onedir')

    if icon_path:
        opts.append(f'--icon={icon_path}')

    # 4. Uruchomienie
    PyInstaller.__main__.run(opts)

    print(f"\n SUKCES! Build gotowy w: {os.path.join(dist_dir, 'StudyPlanner')}")


if __name__ == "__main__":
    build_app()