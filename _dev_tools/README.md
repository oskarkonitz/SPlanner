# DOKUMENTACJA NARZĘDZI DEWELOPERSKICH (_dev_tools)

## 1. STATUS PRAWNY I POCHODZENIE KODU

Niniejszy katalog (_dev_tools) oraz zawarte w nim skrypty **nie stanowią integralnej części właściwego projektu** (aplikacji StudyPlanner). Są to dodatkowe narzędzia pomocnicze służące wyłącznie do:
- Automatyzacji procesu kompilacji (budowania aplikacji).
- Generowania zasobów graficznych (ikon) dla różnych systemów operacyjnych.
- Testowania aplikacji w izolowanych środowiskach.

**NOTA O GENERACJI PRZEZ SZTUCZNĄ INTELIGENCJĘ**
Kod źródłowy zawarty w tym katalogu został w całości wygenerowany przy użyciu modelu językowego AI.

* **Nazwa modelu:** Gemini
* **Typ:** Large Language Model (Google)
* **Data dostępu/generacji:** 15 stycznia 2026
* **Przeznaczenie:** Kod pomocniczy (Build Tools)

---

## 2. ZAWARTOŚĆ KATALOGU

### Skrypty Python
* **`build.py`**
    Główny skrypt automatyzujący proces "zamrażania" kodu (freezing) do pliku wykonywalnego.
    * Wykrywa system operacyjny hosta (Windows / macOS / Linux).
    * Dobiera odpowiednie ścieżki, separatory i formaty ikon.
    * Uruchamia PyInstaller z odpowiednimi flagami.
    * Zarządza strukturą folderu wyjściowego (`planner_build`).

* **`convert_icon.py`**
    Narzędzie graficzne do konwersji plików.
    * Przyjmuje plik źródłowy `source_icon.png`.
    * Generuje plik `.icns` (standard Apple macOS).
    * Generuje plik `.ico` (standard Microsoft Windows).
    * Generuje plik `.png` (standard Linux).

### Zasoby
* **`assets/`**
    Folder przechowujący wynikowe pliki ikon wygenerowane przez `convert_icon.py`. Pliki te są automatycznie pobierane przez skrypt `build.py` podczas kompilacji.

---

## 3. WYMAGANIA SYSTEMOWE

Aby poprawnie uruchomić narzędzia z tego folderu, w środowisku Python muszą być zainstalowane biblioteki zewnętrzne:

1.  `pyinstaller` (do budowania aplikacji)
2.  `pillow` (do przetwarzania grafiki/ikon)

Można je zainstalować komendą:
```bash
pip install pyinstaller pillow