import json
import sqlite3
import datetime
from pathlib import Path
import platformdirs

# --- KONFIGURACJA ---
# False: folder projektu/core | True: folder systemowy (AppData/Config)
USE_SYSTEM_STORAGE = False

# Nazwy aplikacji
APP_NAME = "StudyPlanner"
APP_AUTHOR = "Meimox"

# Ścieżki
CORE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = CORE_DIR / "storage.db"
LOCAL_JSON_PATH = CORE_DIR / "storage.json"  # Potrzebne do migracji

SYSTEM_DIR = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
SYSTEM_DB_PATH = SYSTEM_DIR / "storage.db"
SYSTEM_JSON_PATH = SYSTEM_DIR / "storage.json" # Potrzebne do migracji

if USE_SYSTEM_STORAGE:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = SYSTEM_DB_PATH
    OLD_JSON_PATH = SYSTEM_JSON_PATH
else:
    DB_PATH = LOCAL_DB_PATH
    OLD_JSON_PATH = LOCAL_JSON_PATH

LANG_DIR = CORE_DIR.parent / "languages"

# Domyślne wartości (używane jako fallback)
DEFAULT_DATA = {
    "settings": {
        "max_per_day": 2,
        "max_same_subject_per_day": 1,
        "lang": "en",
        "theme": "dark",
        "next_exam_switch_hour": 24,
        "badge_mode": "default"
    },
    "global_stats": {
        "topics_done": 0,
        "notes_added": 0,
        "exams_added": 0,
        "days_off": 0,
        "pomodoro_sessions": 0,
        "activity_started": False,
        "daily_study_time": 0,
        "last_study_date": "",
        "all_time_best_time": 0,
        "total_study_time": 0,
        "had_overdue": False
    },
    "stats": {"pomodoro_count": 0}
}


class StorageManager:
    def __init__(self, db_path):
        """
        Inicjalizuje managera, tworzy strukturę bazy danych i sprawdza
        czy wymagana jest migracja ze starego formatu JSON.
        """
        self.db_path = db_path
        self._init_db()
        self._check_and_migrate()

    def _get_conn(self):
        """Pomocnicza funkcja zwracająca połączenie z row_factory (używać wewnątrz with)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Tworzy strukturę tabel, jeśli nie istnieją."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id TEXT PRIMARY KEY,
                    subject TEXT,
                    title TEXT,
                    date TEXT,
                    note TEXT,
                    ignore_barrier INTEGER DEFAULT 0,
                    color TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topics (
                    id TEXT PRIMARY KEY,
                    exam_id TEXT,
                    name TEXT,
                    status TEXT,
                    scheduled_date TEXT,
                    locked INTEGER DEFAULT 0,
                    note TEXT,
                    FOREIGN KEY (exam_id) REFERENCES exams (id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_tasks (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    status TEXT,
                    date TEXT,
                    color TEXT,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS global_stats (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blocked_dates (
                    date TEXT PRIMARY KEY
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    achievement_id TEXT PRIMARY KEY,
                    date_earned TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

    # --- MIGRACJA (JSON -> SQL) ---

    def _check_and_migrate(self):
        """Sprawdza czy baza jest pusta i czy istnieje plik JSON do migracji."""
        should_migrate = False
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT count(*) FROM exams")
            if cursor.fetchone()[0] == 0:
                cursor = conn.execute("SELECT count(*) FROM settings")
                if cursor.fetchone()[0] == 0:
                    should_migrate = True

        if should_migrate and OLD_JSON_PATH.exists():
            try:
                print(f"[Storage] Rozpoczynam migrację z {OLD_JSON_PATH}...")
                data = json.loads(OLD_JSON_PATH.read_text(encoding="utf-8"))
                self._migrate_data(data)

                new_name = OLD_JSON_PATH.parent / "storage.json.old"
                OLD_JSON_PATH.rename(new_name)
                print(f"[Storage] Migracja zakończona sukcesem. Stary plik: {new_name}")
            except Exception as e:
                print(f"[Storage] Błąd migracji: {e}")

    def _migrate_data(self, data):
        """Przepisuje dane ze słownika JSON do tabel SQL."""
        today_str = datetime.date.today().isoformat()
        with self._get_conn() as conn:
            # Settings
            if "settings" in data:
                for k, v in data["settings"].items():
                    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, json.dumps(v)))

            # Global Stats
            if "global_stats" in data:
                for k, v in data["global_stats"].items():
                    conn.execute("INSERT OR REPLACE INTO global_stats (key, value) VALUES (?, ?)", (k, json.dumps(v)))

            # Stats
            if "stats" in data:
                for k, v in data["stats"].items():
                    conn.execute("INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (k, json.dumps(v)))

            # Exams
            if "exams" in data:
                for e in data["exams"]:
                    conn.execute("INSERT INTO exams (id, subject, title, date, note, ignore_barrier, color) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (e.get("id"), e.get("subject"), e.get("title"), e.get("date"), e.get("note", ""), 1 if e.get("ignore_barrier") else 0, e.get("color")))

            # Topics
            if "topics" in data:
                for t in data["topics"]:
                    conn.execute("INSERT INTO topics (id, exam_id, name, status, scheduled_date, locked, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                 (t.get("id"), t.get("exam_id"), t.get("name"), t.get("status"), t.get("scheduled_date"), 1 if t.get("locked") else 0, t.get("note", "")))

            # Daily Tasks
            if "daily_tasks" in data:
                for dt in data["daily_tasks"]:
                    conn.execute("INSERT INTO daily_tasks (id, content, status, date, color, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                 (dt.get("id"), dt.get("content"), dt.get("status"), dt.get("date"), dt.get("color"), dt.get("created_at")))

            # Blocked Dates
            if "blocked_dates" in data:
                for d in data["blocked_dates"]:
                    conn.execute("INSERT OR IGNORE INTO blocked_dates (date) VALUES (?)", (d,))

            # Achievements
            if "achievements" in data:
                for ach_id in data["achievements"]:
                    if isinstance(ach_id, str):
                        conn.execute("INSERT OR IGNORE INTO achievements (achievement_id, date_earned) VALUES (?, ?)", (ach_id, today_str))

            conn.commit()

    # --- API (SETTINGS & STATS) ---

    def get_settings(self):
        """Pobiera ustawienia, deserializuje JSON i łączy z domyślnymi."""
        res = {}
        with self._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM settings")
            for r in rows:
                try:
                    res[r["key"]] = json.loads(r["value"])
                except (json.JSONDecodeError, TypeError):
                    res[r["key"]] = r["value"]

        defaults = DEFAULT_DATA["settings"].copy()
        defaults.update(res)
        return defaults

    def update_setting(self, key, value):
        """Aktualizuje pojedyncze ustawienie (zapisuje jako JSON)."""
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    def get_global_stats(self):
        """Pobiera statystyki globalne."""
        res = {}
        with self._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM global_stats")
            for r in rows:
                try:
                    res[r["key"]] = json.loads(r["value"])
                except (json.JSONDecodeError, TypeError):
                    res[r["key"]] = r["value"]

        defaults = DEFAULT_DATA["global_stats"].copy()
        defaults.update(res)
        return defaults

    def update_global_stat(self, key, value):
        """Aktualizuje pojedynczą statystykę globalną."""
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO global_stats (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    def get_other_stats(self):
        """Pobiera dodatkowe statystyki (np. pomodoro_count)."""
        res = {}
        with self._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM stats")
            for r in rows:
                try:
                    res[r["key"]] = json.loads(r["value"])
                except (json.JSONDecodeError, TypeError):
                    res[r["key"]] = r["value"]
        return res

    def update_other_stat(self, key, value):
        """Aktualizuje dodatkową statystykę."""
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    # --- API (EXAMS) ---

    def get_exams(self):
        """Zwraca listę wszystkich egzaminów (sqlite3.Row)."""
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM exams").fetchall()

    def add_exam(self, exam_dict):
        """Dodaje nowy egzamin do bazy."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO exams (id, subject, title, date, note, ignore_barrier, color)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                exam_dict["id"], exam_dict["subject"], exam_dict["title"], exam_dict["date"],
                exam_dict.get("note", ""),
                1 if exam_dict.get("ignore_barrier") else 0,
                exam_dict.get("color")
            ))
            conn.commit()

    def update_exam(self, exam_dict):
        """Aktualizuje istniejący egzamin."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE exams
                SET subject=?, title=?, date=?, note=?, ignore_barrier=?, color=?
                WHERE id = ?
            """, (
                exam_dict["subject"], exam_dict["title"], exam_dict["date"],
                exam_dict.get("note", ""),
                1 if exam_dict.get("ignore_barrier") else 0,
                exam_dict.get("color"),
                exam_dict["id"]
            ))
            conn.commit()

    def delete_exam(self, exam_id):
        """Usuwa egzamin (tematy usuwane kaskadowo)."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM exams WHERE id=?", (exam_id,))
            conn.commit()

    # --- API (TOPICS) ---

    def get_topics(self, exam_id=None):
        """Zwraca listę tematów dla danego egzaminu lub wszystkie."""
        with self._get_conn() as conn:
            if exam_id:
                return conn.execute("SELECT * FROM topics WHERE exam_id=?", (exam_id,)).fetchall()
            else:
                return conn.execute("SELECT * FROM topics").fetchall()

    def add_topic(self, topic_dict):
        """Dodaje nowy temat."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO topics (id, exam_id, name, status, scheduled_date, locked, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                topic_dict["id"], topic_dict["exam_id"], topic_dict["name"], topic_dict["status"],
                topic_dict.get("scheduled_date"),
                1 if topic_dict.get("locked") else 0,
                topic_dict.get("note", "")
            ))
            conn.commit()

    def update_topic(self, topic_dict):
        """Aktualizuje istniejący temat."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE topics
                SET exam_id=?, name=?, status=?, scheduled_date=?, locked=?, note=?
                WHERE id = ?
            """, (
                topic_dict["exam_id"], topic_dict["name"], topic_dict["status"],
                topic_dict.get("scheduled_date"),
                1 if topic_dict.get("locked") else 0,
                topic_dict.get("note", ""),
                topic_dict["id"]
            ))
            conn.commit()

    def delete_topic(self, topic_id):
        """Usuwa temat."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM topics WHERE id=?", (topic_id,))
            conn.commit()

    # --- API (DAILY TASKS) ---

    def get_daily_tasks(self):
        """Zwraca listę zadań dziennych."""
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM daily_tasks").fetchall()

    def add_daily_task(self, task_dict):
        """Dodaje nowe zadanie dzienne."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO daily_tasks (id, content, status, date, color, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task_dict["id"], task_dict["content"], task_dict["status"],
                task_dict["date"], task_dict.get("color"), task_dict.get("created_at")
            ))
            conn.commit()

    def update_daily_task(self, task_dict):
        """Aktualizuje zadanie dzienne."""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE daily_tasks
                SET content=?, status=?, date=?, color=?, created_at=?
                WHERE id = ?
            """, (
                task_dict["content"], task_dict["status"], task_dict["date"],
                task_dict.get("color"), task_dict.get("created_at"),
                task_dict["id"]
            ))
            conn.commit()

    def delete_daily_task(self, task_id):
        """Usuwa zadanie dzienne."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM daily_tasks WHERE id=?", (task_id,))
            conn.commit()

    # --- API (OTHERS) ---

    def get_blocked_dates(self):
        """Zwraca listę zablokowanych dat (lista stringów)."""
        with self._get_conn() as conn:
            return [row["date"] for row in conn.execute("SELECT date FROM blocked_dates")]

    def add_blocked_date(self, date_str):
        """Dodaje datę do zablokowanych."""
        with self._get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO blocked_dates (date) VALUES (?)", (date_str,))
            conn.commit()

    def remove_blocked_date(self, date_str):
        """Usuwa datę z zablokowanych."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM blocked_dates WHERE date=?", (date_str,))
            conn.commit()

    def get_achievements(self):
        """Zwraca listę ID zdobytych osiągnięć."""
        with self._get_conn() as conn:
            return [row["achievement_id"] for row in conn.execute("SELECT achievement_id FROM achievements")]

    def add_achievement(self, achievement_id):
        """Dodaje osiągnięcie z dzisiejszą datą."""
        today = datetime.date.today().isoformat()
        with self._get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO achievements (achievement_id, date_earned) VALUES (?, ?)",
                         (achievement_id, today))
            conn.commit()


# Inicjalizacja Managera (Singleton w obrębie modułu)
manager = StorageManager(DB_PATH)


def load_language(lang_code="en"):
    """Ładuje plik językowy JSON (funkcja pomocnicza)."""
    file_path = LANG_DIR / f"lang_{lang_code}.json"
    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))

    alternative_path = LANG_DIR / "lang_en.json"
    if alternative_path.exists():
        return json.loads(alternative_path.read_text(encoding="utf-8"))
    return {}