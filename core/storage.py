import json
from pathlib import Path
import platformdirs

#   KONFIGURACJA:
#       - False, jesli dane maja byc zapisywane w folderze projektu/core
#       - True, jesli dane maja byc zapisywane w folderach systemowych

USE_SYSTEM_STORAGE = False

# sciezka lokalna
CORE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = CORE_DIR / "storage.json"

# sciezka systemowa
APP_NAME = "StudyPlanner"
APP_AUTHOR = "Meimox"
SYSTEM_DIR = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
SYSTEM_DB_PATH = SYSTEM_DIR / "storage.json"

# wybor sciezki na podstawie USE_SYSTEM_STORAGE
if USE_SYSTEM_STORAGE:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True) #upewnienie sie ze folder istnieje
    DB_PATH = SYSTEM_DB_PATH
else:
    DB_PATH = LOCAL_DB_PATH

# sciezka folderu z jezykami
LANG_DIR = CORE_DIR.parent / "languages"

# domyslne dane do zapisania w pliku storage.json jesli dopiero sie go tworzy
DEFAULT_DATA = {
    "settings": {
        "max_per_day": 2,
        "max_same_subject_per_day": 1,
        "lang": "en"
    },
    "exams": [],
    "topics": []
}

#   FUNKCJA WCZYTUJACA BAZE DANYCH PROGRAMU
def load(path=DB_PATH):
    p = Path(path)
    if not p.exists():
        return DEFAULT_DATA.copy()
    return json.loads(p.read_text(encoding="utf-8"))

#   FUNKCJA ZAPISUJACA DANE Z PROGRAMU DO BAZY DANYCH
def save(data, path=DB_PATH):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

#   FUNKCJA WCZYTUJACA JEZYK W JAKIM PROGRAM MA ZOSTAC WYSWIETLONY
def load_language(lang_code="en"):
    file_path = LANG_DIR / f"lang_{lang_code}.json"

    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))

    # awaryjnie jesli funkcja dostanie nieistniejacy kod jezyka to ustawi domyslnie angielski
    alternative_path = LANG_DIR / "lang_en.json"
    if alternative_path.exists():
        return json.loads(alternative_path.read_text(encoding="utf-8"))

    # jesli brakuje danych jezykowy to zwroci puste dany zeby program sie nie wywalil
    return {}
