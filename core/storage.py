import json
from pathlib import Path
import platformdirs

#   KONFIGURACJA:
#       - False, jesli dane maja byc zapisywane w folderze projektu/core
#       - True, jesli dane maja byc zapisywane w folderach systemowych

USE_SYSTEM_STORAGE = True

# sciezka lokalna
CORE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = CORE_DIR / "storage.json"

# sciezka systemowa
APP_NAME = "StudyPlanner"
APP_AUTHOR = "Meimox"
SYSTEM_DIR = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
SYSTEM_DB_PATH = SYSTEM_DIR / "storage.json"

if USE_SYSTEM_STORAGE:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = SYSTEM_DB_PATH
else:
    DB_PATH = LOCAL_DB_PATH

LANG_DIR = CORE_DIR.parent / "languages"

DEFAULT_DATA = {
    "settings": {
        "max_per_day": 2,
        "max_same_subject_per_day": 1,
        "lang": "en",
        "theme": "dark",
        "next_exam_switch_hour": 24
    },
    "global_stats": {
        "topics_done": 0,
        "notes_added": 0,
        "exams_added": 0,
        "days_off": 0,
        "pomodoro_sessions": 0,
        "activity_started": False,
        "daily_study_time": 0,  # <--- NOWE: Czas w sekundach (dzisiaj)
        "last_study_date": "",  # <--- NOWE: Data ostatniego resetu
        "all_time_best_time": 0,  # <--- NOWE: Rekord dzienny
        "total_study_time": 0  # <--- NOWE: Czas całkowity (od początku używania)
    },
    "blocked_dates": [],
    "exams": [],
    "topics": [],
    "daily_tasks": []
}


def load(path=DB_PATH):
    p = Path(path)
    if not p.exists():
        return DEFAULT_DATA.copy()
    return json.loads(p.read_text(encoding="utf-8"))


def save(data, path=DB_PATH):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def load_language(lang_code="en"):
    file_path = LANG_DIR / f"lang_{lang_code}.json"
    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))

    alternative_path = LANG_DIR / "lang_en.json"
    if alternative_path.exists():
        return json.loads(alternative_path.read_text(encoding="utf-8"))
    return {}