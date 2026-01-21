# PROJEKT WDP - Aplikacja do zarzadzania nauką



## OPIS PROJEKTU
Zródła i informacje z podziałem na pliki:

### `storage.py`

1. **Materiały pomocnicze:**
- pathlib https://docs.python.org/3/library/pathlib.html
- json https://docs.python.org/3/library/json.html
- platformdirs https://pypi.org/project/platformdirs/


2. **Opis kodu:**

`storage.py` zawiera 3 główne funkcje:
- load - sluży do wczytywania bazy danych z pliku json dla dalszej części programu
- save - służy do zapisywania bazy danych operacji wykonanych przez program albo użytkownika
- load_language - wczytuje plik ze zmiennymi językowymi (zapisanymi w json jako słowniki)
   

3. **Sposób pisania:**
- funkcje `load`,`save`,`load_language` napisałem samodzielnie z pomocą materiałów pomocniczych jak działa pathlib i jak obslugiwać pliki json, linki do stron u góry. Dodatkowo użyłem Google Gemini podpowiedział mi aby w `save` ustawić `default=str` aby formaty się zgadzały i nie powodowały błedów oraz aby zabezpieczyć funkcje `load_languages` przed dostaniem nieistniejącego kodu języka.
- Początkowe fragmenty kodu są napisane przez Google Gemini i służą rozpoznawaniu w jakim systemie uruchomiono program oraz ustalają ścieżke bazy danych. Zrobione jest to dla plików w `_dev_tools`(które nie są częścią projektu, a służą do eksportowania aplikacji do pliku wykonywalnego. Oznaczone `*`). Fragmenty z opisami poniżej:

`*`Przełącznik True / False | mówi programowi czy ma korzystać z bazy danych zapisanej w pliku projektu czy w folderach systemowych:
```
USE_SYSTEM_STORAGE = True
```
`*`Ustalenie gdzie znajduje się baza danych. Lokalna - projekt, systemowa - w katalogu systemowym
```
CORE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = CORE_DIR / "storage.json"

APP_NAME = "StudyPlanner"
APP_AUTHOR = "Meimox"
SYSTEM_DIR = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
SYSTEM_DB_PATH = SYSTEM_DIR / "storage.json"
```
`*`Wybór z której ściezki program ma korzystać na podstawie `USE_SYSTEM_STORAGE`
```
if USE_SYSTEM_STORAGE:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = SYSTEM_DB_PATH
else:
    DB_PATH = LOCAL_DB_PATH
```
Znalezienie gdzie znajdują się pliki z językami:
```
LANG_DIR = CORE_DIR.parent / "languages"
```