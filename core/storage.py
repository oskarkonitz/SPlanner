import json
import sqlite3
import datetime
import uuid
from pathlib import Path
import platformdirs
from abc import ABC, abstractmethod
import threading

# Próba importu supabase
try:
    from supabase import create_client, Client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# --- KONFIGURACJA ŚRODOWISKA ---
USE_SYSTEM_STORAGE = True

# Nazwy aplikacji
APP_NAME = "StudyPlanner"
APP_AUTHOR = "Meimox"

# Ścieżki
CORE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = CORE_DIR / "storage.db"
LOCAL_JSON_PATH = CORE_DIR / "storage.json"
LOCAL_CONFIG_PATH = CORE_DIR / "config.json"

SYSTEM_DIR = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
SYSTEM_DB_PATH = SYSTEM_DIR / "storage.db"
SYSTEM_JSON_PATH = SYSTEM_DIR / "storage.json"
SYSTEM_CONFIG_PATH = SYSTEM_DIR / "config.json"

if USE_SYSTEM_STORAGE:
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = SYSTEM_DB_PATH
    OLD_JSON_PATH = SYSTEM_JSON_PATH
    CONFIG_PATH = SYSTEM_CONFIG_PATH
else:
    DB_PATH = LOCAL_DB_PATH
    OLD_JSON_PATH = LOCAL_JSON_PATH
    CONFIG_PATH = LOCAL_CONFIG_PATH

LANG_DIR = CORE_DIR.parent / "languages"

# --- DOMYŚLNE WARTOŚCI ---
DEFAULT_DATA = {
    "settings": {
        "max_per_day": 2,
        "max_same_subject_per_day": 1,
        "lang": "en",
        "theme": "dark",
        "next_exam_switch_hour": 24,
        "badge_mode": "default",
        "schedule_use_full_name": False,
        "schedule_show_times": False,
        "schedule_show_room": True,
        "grading_system": {
            "grade_mode": "percentage",
            "weight_mode": "percentage",
            "pass_threshold": 50
        },
        "sound_timer_finish": "def_level_up",
        "sound_achievement": "def_coin",
        "sound_all_done": "def_fanfare",
        "sound_enabled": True,
        "sound_volume": 0.5
    },
    "global_stats": {
        "topics_done": 0, "notes_added": 0, "exams_added": 0, "days_off": 0,
        "pomodoro_sessions": 0, "activity_started": False, "daily_study_time": 0,
        "last_study_date": "", "all_time_best_time": 0, "total_study_time": 0,
        "had_overdue": False
    },
    "stats": {"pomodoro_count": 0}
}

DEFAULT_SOUNDS = [
    {
        "id": "def_coin", "name": "Retro Coin",
        "steps": [{"freq": 988, "dur": 0.08, "type": "Square"}, {"freq": 1319, "dur": 0.35, "type": "Square"}]
    },
    {
        "id": "def_level_up", "name": "Level Up!",
        "steps": [{"freq": 523, "dur": 0.1, "type": "Square"}, {"freq": 659, "dur": 0.1, "type": "Square"},
                  {"freq": 784, "dur": 0.1, "type": "Square"}, {"freq": 1046, "dur": 0.1, "type": "Square"},
                  {"freq": 784, "dur": 0.1, "type": "Square"}, {"freq": 1046, "dur": 0.4, "type": "Square"}]
    },
    {
        "id": "def_fanfare", "name": "Victory Fanfare",
        "steps": [{"freq": 523, "dur": 0.15, "type": "Square"}, {"freq": 659, "dur": 0.15, "type": "Square"},
                  {"freq": 784, "dur": 0.15, "type": "Square"}, {"freq": 1046, "dur": 0.6, "type": "Square"}]
    }
]

# --- SKRYPT SQL DLA SUPABASE ---
SQL_SCHEMA = """
             -- 1. KONFIGURACJA I STATYSTYKI
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY, 
    value JSONB
);

CREATE TABLE IF NOT EXISTS global_stats (
    key TEXT PRIMARY KEY, 
    value JSONB
);

CREATE TABLE IF NOT EXISTS stats (
    key TEXT PRIMARY KEY, 
    value JSONB
);

CREATE TABLE IF NOT EXISTS achievements (
    achievement_id TEXT PRIMARY KEY, 
    date_earned DATE
);

CREATE TABLE IF NOT EXISTS blocked_dates (
    date DATE PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS custom_sounds (
    id TEXT PRIMARY KEY, 
    name TEXT, 
    steps_json JSONB
);

-- 2. STRUKTURA AKADEMICKA
CREATE TABLE IF NOT EXISTS semesters (
    id TEXT PRIMARY KEY,
    name TEXT,
    start_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS subjects (
    id TEXT PRIMARY KEY,
    semester_id TEXT REFERENCES semesters(id) ON DELETE CASCADE,
    name TEXT,
    short_name TEXT,
    color TEXT,
    weight REAL DEFAULT 1.0,
    start_datetime TEXT,
    end_datetime TEXT
);

-- 3. GRAFIK (CUSTOM EVENTS) - TWOJA NOWOŚĆ
CREATE TABLE IF NOT EXISTS event_lists (
    id TEXT PRIMARY KEY,
    name TEXT,
    color TEXT
);

CREATE TABLE IF NOT EXISTS custom_events (
    id TEXT PRIMARY KEY,
    list_id TEXT REFERENCES event_lists(id) ON DELETE SET NULL,
    title TEXT,
    is_recurring BOOLEAN DEFAULT FALSE,
    date DATE,
    day_of_week INTEGER,
    start_time TEXT,
    end_time TEXT,
    start_date DATE,
    end_date DATE,
    color TEXT
);

-- 4. EGZAMINY I TEMATY
CREATE TABLE IF NOT EXISTS exams (
    id TEXT PRIMARY KEY,
    subject_id TEXT REFERENCES subjects(id) ON DELETE SET NULL,
    subject TEXT,
    title TEXT,
    date DATE,
    time TEXT,
    note TEXT,
    ignore_barrier BOOLEAN DEFAULT FALSE,
    color TEXT
);

CREATE TABLE IF NOT EXISTS topics (
    id TEXT PRIMARY KEY,
    exam_id TEXT REFERENCES exams(id) ON DELETE CASCADE,
    name TEXT,
    status TEXT,
    scheduled_date DATE,
    locked BOOLEAN DEFAULT FALSE,
    note TEXT
);

-- 5. OCENY I MODUŁY
CREATE TABLE IF NOT EXISTS grade_modules (
    id TEXT PRIMARY KEY,
    subject_id TEXT REFERENCES subjects(id) ON DELETE CASCADE,
    name TEXT,
    weight REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS grades (
    id TEXT PRIMARY KEY,
    subject_id TEXT REFERENCES subjects(id) ON DELETE CASCADE,
    module_id TEXT REFERENCES grade_modules(id) ON DELETE SET NULL,
    value REAL,
    weight REAL DEFAULT 1.0,
    desc_text TEXT,
    date DATE
);

-- 6. PLAN LEKCJI I ZADANIA CODZIENNE
CREATE TABLE IF NOT EXISTS task_lists (
    id TEXT PRIMARY KEY, 
    name TEXT, 
    icon TEXT
);

CREATE TABLE IF NOT EXISTS daily_tasks (
    id TEXT PRIMARY KEY,
    content TEXT,
    status TEXT,
    date DATE,
    color TEXT,
    created_at TEXT,
    note TEXT,
    list_id TEXT REFERENCES task_lists(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS schedule_entries (
    id TEXT PRIMARY KEY,
    subject_id TEXT REFERENCES subjects(id) ON DELETE CASCADE,
    day_of_week INTEGER,
    start_time TEXT,
    end_time TEXT,
    room TEXT,
    type TEXT,
    period_start DATE,
    period_end DATE
);

CREATE TABLE IF NOT EXISTS schedule_cancellations (
    id TEXT PRIMARY KEY,
    entry_id TEXT REFERENCES schedule_entries(id) ON DELETE CASCADE,
    date DATE
);
             """


# --- ABSTRAKCYJNY DOSTAWCA DANYCH ---
class BaseProvider(ABC):
    @abstractmethod
    def get_settings(self): pass

    @abstractmethod
    def update_setting(self, key, value): pass

    @abstractmethod
    def get_global_stats(self): pass

    @abstractmethod
    def update_global_stat(self, key, value): pass

    @abstractmethod
    def get_other_stats(self): pass

    @abstractmethod
    def update_other_stat(self, key, value): pass

    @abstractmethod
    def get_custom_sounds(self): pass

    @abstractmethod
    def get_custom_sound(self, sound_id): pass

    @abstractmethod
    def add_custom_sound(self, sound_dict): pass

    @abstractmethod
    def delete_custom_sound(self, sound_id): pass

    @abstractmethod
    def get_exam(self, exam_id): pass

    @abstractmethod
    def get_exams(self): pass

    @abstractmethod
    def add_exam(self, exam_dict): pass

    @abstractmethod
    def update_exam(self, exam_dict): pass

    @abstractmethod
    def delete_exam(self, exam_id): pass

    @abstractmethod
    def get_topic(self, topic_id): pass

    @abstractmethod
    def get_topics(self, exam_id=None): pass

    @abstractmethod
    def add_topic(self, topic_dict): pass

    @abstractmethod
    def update_topic(self, topic_dict): pass

    @abstractmethod
    def update_topics_bulk(self, topics_list): pass  # NOWOŚĆ: Hurtowa aktualizacja

    @abstractmethod
    def delete_topic(self, topic_id): pass

    @abstractmethod
    def get_task_lists(self): pass

    @abstractmethod
    def add_task_list(self, list_dict): pass

    @abstractmethod
    def delete_task_list(self, list_id): pass

    @abstractmethod
    def get_daily_task(self, task_id): pass

    @abstractmethod
    def get_daily_tasks(self): pass

    @abstractmethod
    def add_daily_task(self, task_dict): pass

    @abstractmethod
    def update_daily_task(self, task_dict): pass

    @abstractmethod
    def delete_daily_task(self, task_id): pass

    @abstractmethod
    def get_blocked_dates(self): pass

    @abstractmethod
    def add_blocked_date(self, date_str): pass

    @abstractmethod
    def remove_blocked_date(self, date_str): pass

    @abstractmethod
    def get_achievements(self): pass

    @abstractmethod
    def add_achievement(self, achievement_id): pass

    @abstractmethod
    def get_semesters(self): pass

    @abstractmethod
    def add_semester(self, sem_dict): pass

    @abstractmethod
    def update_semester(self, sem_dict): pass

    @abstractmethod
    def delete_semester(self, sem_id): pass

    @abstractmethod
    def get_subjects(self, semester_id=None): pass

    @abstractmethod
    def add_subject(self, sub_dict): pass

    @abstractmethod
    def update_subject(self, sub_dict): pass

    @abstractmethod
    def delete_subject(self, sub_id): pass

    @abstractmethod
    def get_schedule(self): pass

    @abstractmethod
    def get_schedule_entries_by_subject(self, subject_id): pass

    @abstractmethod
    def add_schedule_entry(self, entry_dict): pass

    @abstractmethod
    def delete_schedule_entry(self, entry_id): pass

    @abstractmethod
    def add_schedule_cancellation(self, entry_id, date_str): pass

    @abstractmethod
    def get_schedule_cancellations(self): pass

    @abstractmethod
    def get_grades(self, subject_id=None): pass

    @abstractmethod
    def add_grade(self, grade_dict): pass

    @abstractmethod
    def delete_grade(self, grade_id): pass

    @abstractmethod
    def get_grade_modules(self, subject_id): pass

    @abstractmethod
    def add_grade_module(self, module_dict): pass

    @abstractmethod
    def update_grade_module(self, module_dict): pass

    @abstractmethod
    def delete_grade_module(self, module_id): pass

    @abstractmethod
    def get_task_history(self): pass

    @abstractmethod
    def clear_task_history(self, today_str): pass

    @abstractmethod
    def restore_overdue_tasks(self, today_str): pass


# --- DOSTAWCA: LOKALNY SQLITE ---
class SQLiteProvider(BaseProvider):
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()
        self._check_migrations()
        self._ensure_default_sounds()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=20)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS exams
            (
                id
                TEXT
                PRIMARY
                KEY,
                subject_id
                TEXT,
                subject
                TEXT,
                title
                TEXT,
                date
                TEXT,
                time
                TEXT,
                note
                TEXT,
                ignore_barrier
                INTEGER
                DEFAULT
                0,
                color
                TEXT,
                FOREIGN
                KEY
                            (
                subject_id
                            ) REFERENCES subjects
                            (
                                id
                            ) ON DELETE SET NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS topics
            (
                id
                TEXT
                PRIMARY
                KEY,
                exam_id
                TEXT,
                name
                TEXT,
                status
                TEXT,
                scheduled_date
                TEXT,
                locked
                INTEGER
                DEFAULT
                0,
                note
                TEXT,
                FOREIGN
                KEY
                            (
                exam_id
                            ) REFERENCES exams
                            (
                                id
                            ) ON DELETE CASCADE)""")
            conn.execute("CREATE TABLE IF NOT EXISTS task_lists (id TEXT PRIMARY KEY, name TEXT, icon TEXT)")
            conn.execute("""CREATE TABLE IF NOT EXISTS daily_tasks
                            (
                                id
                                TEXT
                                PRIMARY
                                KEY,
                                content
                                TEXT,
                                status
                                TEXT,
                                date
                                TEXT,
                                color
                                TEXT,
                                created_at
                                TEXT,
                                note
                                TEXT,
                                list_id
                                TEXT
                            )""")
            try:
                conn.execute("ALTER TABLE daily_tasks ADD COLUMN note TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute("ALTER TABLE daily_tasks ADD COLUMN list_id TEXT")
            except sqlite3.OperationalError:
                pass
            conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS global_stats (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS blocked_dates (date TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE IF NOT EXISTS achievements (achievement_id TEXT PRIMARY KEY, date_earned TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("""CREATE TABLE IF NOT EXISTS semesters
                            (
                                id
                                TEXT
                                PRIMARY
                                KEY,
                                name
                                TEXT,
                                start_date
                                TEXT,
                                end_date
                                TEXT,
                                is_current
                                INTEGER
                                DEFAULT
                                0
                            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS subjects
            (
                id
                TEXT
                PRIMARY
                KEY,
                semester_id
                TEXT,
                name
                TEXT,
                short_name
                TEXT,
                color
                TEXT,
                weight
                REAL
                DEFAULT
                1.0,
                start_datetime
                TEXT,
                end_datetime
                TEXT,
                FOREIGN
                KEY
                            (
                semester_id
                            ) REFERENCES semesters
                            (
                                id
                            ) ON DELETE CASCADE)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS schedule_entries
            (
                id
                TEXT
                PRIMARY
                KEY,
                subject_id
                TEXT,
                day_of_week
                INTEGER,
                start_time
                TEXT,
                end_time
                TEXT,
                room
                TEXT,
                type
                TEXT,
                period_start
                TEXT,
                period_end
                TEXT,
                FOREIGN
                KEY
                            (
                subject_id
                            ) REFERENCES subjects
                            (
                                id
                            ) ON DELETE CASCADE)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS schedule_cancellations
            (
                id
                TEXT
                PRIMARY
                KEY,
                entry_id
                TEXT,
                date
                TEXT,
                FOREIGN
                KEY
                            (
                entry_id
                            ) REFERENCES schedule_entries
                            (
                                id
                            ) ON DELETE CASCADE)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS grade_modules
            (
                id
                TEXT
                PRIMARY
                KEY,
                subject_id
                TEXT,
                name
                TEXT,
                weight
                REAL
                DEFAULT
                0.0,
                FOREIGN
                KEY
                            (
                subject_id
                            ) REFERENCES subjects
                            (
                                id
                            ) ON DELETE CASCADE)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS grades
            (
                id
                TEXT
                PRIMARY
                KEY,
                subject_id
                TEXT,
                module_id
                TEXT,
                value
                REAL,
                weight
                REAL
                DEFAULT
                1.0,
                desc
                TEXT,
                date
                TEXT,
                FOREIGN
                KEY
                            (
                subject_id
                            ) REFERENCES subjects
                            (
                                id
                            ) ON DELETE CASCADE, FOREIGN KEY
                            (
                                module_id
                            ) REFERENCES grade_modules
                            (
                                id
                            )
                              ON DELETE SET NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS custom_sounds
                            (
                                id
                                TEXT
                                PRIMARY
                                KEY,
                                name
                                TEXT,
                                steps_json
                                TEXT
                            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS event_lists
                            (
                                id
                                TEXT
                                PRIMARY
                                KEY,
                                name
                                TEXT,
                                color
                                TEXT
                            )""")

            conn.execute("""CREATE TABLE IF NOT EXISTS custom_events
                            (
                                id
                                TEXT
                                PRIMARY
                                KEY,
                                list_id
                                TEXT,
                                title
                                TEXT,
                                is_recurring
                                INTEGER,
                                date
                                TEXT,
                                day_of_week
                                INTEGER,
                                start_time
                                TEXT,
                                end_time
                                TEXT,
                                start_date
                                TEXT,
                                end_date
                                TEXT,
                                color
                                TEXT
                            )""")
            try:
                conn.execute(
                    "ALTER TABLE grades ADD COLUMN module_id TEXT REFERENCES grade_modules(id) ON DELETE SET NULL")
            except sqlite3.OperationalError:
                pass

    def _ensure_default_sounds(self):
        with self._get_conn() as conn:
            for sound in DEFAULT_SOUNDS:
                exists = conn.execute("SELECT 1 FROM custom_sounds WHERE id=?", (sound["id"],)).fetchone()
                if not exists:
                    conn.execute("INSERT INTO custom_sounds (id, name, steps_json) VALUES (?, ?, ?)",
                                 (sound["id"], sound["name"], json.dumps(sound["steps"])))
            conn.commit()

    def _check_migrations(self):
        should_migrate_json = False
        with self._get_conn() as conn:
            if conn.execute("SELECT count(*) FROM exams").fetchone()[0] == 0:
                if conn.execute("SELECT count(*) FROM settings").fetchone()[0] == 0:
                    should_migrate_json = True
        if should_migrate_json and OLD_JSON_PATH.exists(): self._migrate_json_to_sql()
        self._migrate_to_relational_schema()
        self._migrate_subjects_add_dates()
        self._migrate_exams_add_time()

    def _migrate_json_to_sql(self):
        try:
            data = json.loads(OLD_JSON_PATH.read_text(encoding="utf-8"))
            today_str = datetime.date.today().isoformat()
            with self._get_conn() as conn:
                if "settings" in data:
                    for k, v in data["settings"].items(): conn.execute(
                        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, json.dumps(v)))
                if "global_stats" in data:
                    for k, v in data["global_stats"].items(): conn.execute(
                        "INSERT OR REPLACE INTO global_stats (key, value) VALUES (?, ?)", (k, json.dumps(v)))
                if "stats" in data:
                    for k, v in data["stats"].items(): conn.execute(
                        "INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (k, json.dumps(v)))
                if "exams" in data:
                    for e in data["exams"]: conn.execute(
                        "INSERT INTO exams (id, subject, title, date, note, ignore_barrier, color) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (e.get("id"), e.get("subject"), e.get("title"), e.get("date"), e.get("note", ""),
                         1 if e.get("ignore_barrier") else 0, e.get("color")))
                if "topics" in data:
                    for t in data["topics"]: conn.execute(
                        "INSERT INTO topics (id, exam_id, name, status, scheduled_date, locked, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (t.get("id"), t.get("exam_id"), t.get("name"), t.get("status"), t.get("scheduled_date"),
                         1 if t.get("locked") else 0, t.get("note", "")))
                if "daily_tasks" in data:
                    for dt in data["daily_tasks"]: conn.execute(
                        "INSERT INTO daily_tasks (id, content, status, date, color, created_at, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (dt.get("id"), dt.get("content"), dt.get("status"), dt.get("date"), dt.get("color"),
                         dt.get("created_at"), dt.get("note", "")))
                if "blocked_dates" in data:
                    for d in data["blocked_dates"]: conn.execute(
                        "INSERT OR IGNORE INTO blocked_dates (date) VALUES (?)", (d,))
                if "achievements" in data:
                    for ach_id in data["achievements"]:
                        if isinstance(ach_id, str): conn.execute(
                            "INSERT OR IGNORE INTO achievements (achievement_id, date_earned) VALUES (?, ?)",
                            (ach_id, today_str))
                conn.commit()
            new_name = OLD_JSON_PATH.parent / "storage.json"
            OLD_JSON_PATH.rename(new_name)
        except Exception:
            pass

    def _migrate_to_relational_schema(self):
        with self._get_conn() as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(exams)")]
            if "subject_id" not in columns:
                try:
                    conn.execute(
                        "ALTER TABLE exams ADD COLUMN subject_id TEXT REFERENCES subjects(id) ON DELETE SET NULL")
                except sqlite3.OperationalError:
                    pass
            exams_to_fix = conn.execute(
                "SELECT id, subject FROM exams WHERE subject_id IS NULL AND subject IS NOT NULL").fetchall()
            if not exams_to_fix: return
            default_sem_id = f"sem_{uuid.uuid4().hex[:8]}"
            existing_sem = conn.execute("SELECT id FROM semesters LIMIT 1").fetchone()
            if existing_sem:
                current_sem_id = existing_sem[0]
            else:
                conn.execute(
                    "INSERT INTO semesters (id, name, start_date, end_date, is_current) VALUES (?, ?, ?, ?, ?)",
                    (default_sem_id, "Domyślny (Migracja)", str(datetime.date.today()),
                     str(datetime.date.today().replace(year=datetime.date.today().year + 1)), 1))
                current_sem_id = default_sem_id
            unique_subjects = set(e["subject"] for e in exams_to_fix)
            subject_map = {}
            for name in unique_subjects:
                existing_subj = conn.execute("SELECT id FROM subjects WHERE name=? ", (name,)).fetchone()
                if existing_subj:
                    subject_map[name] = existing_subj[0]
                else:
                    new_sub_id = f"sub_{uuid.uuid4().hex[:8]}"
                    short = "".join([word[0].upper() for word in name.split() if word])[:3]
                    conn.execute(
                        "INSERT INTO subjects (id, semester_id, name, short_name, color, weight) VALUES (?, ?, ?, ?, ?, ?)",
                        (new_sub_id, current_sem_id, name, short, None, 1.0))
                    subject_map[name] = new_sub_id
            for exam in exams_to_fix:
                if exam["subject"] in subject_map:
                    conn.execute("UPDATE exams SET subject_id=? WHERE id=?", (subject_map[exam["subject"]], exam["id"]))
            conn.commit()

    def _migrate_subjects_add_dates(self):
        with self._get_conn() as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(subjects)")]
            if "start_datetime" not in columns:
                try:
                    conn.execute("ALTER TABLE subjects ADD COLUMN start_datetime TEXT")
                except sqlite3.OperationalError:
                    pass
            if "end_datetime" not in columns:
                try:
                    conn.execute("ALTER TABLE subjects ADD COLUMN end_datetime TEXT")
                except sqlite3.OperationalError:
                    pass
            conn.commit()

    def _migrate_exams_add_time(self):
        with self._get_conn() as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(exams)")]
            if "time" not in columns:
                try:
                    conn.execute("ALTER TABLE exams ADD COLUMN time TEXT")
                except sqlite3.OperationalError:
                    pass
            conn.commit()

    def get_settings(self):
        res = {}
        with self._get_conn() as conn:
            for r in conn.execute("SELECT key, value FROM settings"):
                try:
                    res[r["key"]] = json.loads(r["value"])
                except:
                    res[r["key"]] = r["value"]
        defaults = DEFAULT_DATA["settings"].copy()
        for k, v in res.items():
            if k in defaults and isinstance(defaults[k], dict) and isinstance(v, dict):
                defaults[k].update(v)
            else:
                defaults[k] = v
        return defaults

    def update_setting(self, key, value):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    def get_global_stats(self):
        res = {}
        with self._get_conn() as conn:
            for r in conn.execute("SELECT key, value FROM global_stats"):
                try:
                    res[r["key"]] = json.loads(r["value"])
                except:
                    res[r["key"]] = r["value"]
        defaults = DEFAULT_DATA["global_stats"].copy()
        defaults.update(res)
        return defaults

    def update_global_stat(self, key, value):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO global_stats (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    def get_other_stats(self):
        res = {}
        with self._get_conn() as conn:
            for r in conn.execute("SELECT key, value FROM stats"):
                try:
                    res[r["key"]] = json.loads(r["value"])
                except:
                    res[r["key"]] = r["value"]
        return res

    def update_other_stat(self, key, value):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    def get_custom_sounds(self):
        with self._get_conn() as conn:
            results = []
            for r in conn.execute("SELECT * FROM custom_sounds").fetchall():
                d = dict(r)
                try:
                    d["steps"] = json.loads(d["steps_json"])
                except:
                    d["steps"] = []
                del d["steps_json"]
                results.append(d)
            return results

    def get_custom_sound(self, sound_id):
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM custom_sounds WHERE id=?", (sound_id,)).fetchone()
            if row:
                d = dict(row)
                try:
                    d["steps"] = json.loads(d["steps_json"])
                except:
                    d["steps"] = []
                return d
            return None

    def add_custom_sound(self, sound_dict):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO custom_sounds (id, name, steps_json) VALUES (?, ?, ?)",
                         (sound_dict["id"], sound_dict["name"], json.dumps(sound_dict["steps"])))
            conn.commit()

    def delete_custom_sound(self, sound_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM custom_sounds WHERE id=?", (sound_id,))
            conn.commit()

    def get_exam(self, exam_id):
        sql = "SELECT e.*, s.name as subject_name, s.color as subject_color FROM exams e LEFT JOIN subjects s ON e.subject_id = s.id WHERE e.id = ?"
        with self._get_conn() as conn:
            row = conn.execute(sql, (exam_id,)).fetchone()
            if row:
                data = dict(row)
                data["ignore_barrier"] = bool(data["ignore_barrier"])
                if data.get("subject_name"): data["subject"] = data["subject_name"]
                return data
            return None

    def get_exams(self):
        sql = "SELECT e.*, s.name as subject_name, s.color as subject_color FROM exams e LEFT JOIN subjects s ON e.subject_id = s.id"
        with self._get_conn() as conn:
            results = []
            for r in conn.execute(sql).fetchall():
                d = dict(r)
                if d.get("subject_name"): d["subject"] = d["subject_name"]
                if d.get("subject_color"): d["color"] = d["subject_color"]
                results.append(d)
            return results

    def add_exam(self, exam_dict):
        with self._get_conn() as conn:
            subj_id = exam_dict.get("subject_id")
            if not subj_id and exam_dict.get("subject"):
                row = conn.execute("SELECT id FROM subjects WHERE name=?", (exam_dict["subject"],)).fetchone()
                if row:
                    subj_id = row[0]
                else:
                    sem = conn.execute("SELECT id FROM semesters LIMIT 1").fetchone()
                    if sem:
                        new_sid = f"sub_{uuid.uuid4().hex[:8]}"
                        conn.execute(
                            "INSERT INTO subjects (id, semester_id, name, short_name, color) VALUES (?, ?, ?, ?, ?)",
                            (new_sid, sem[0], exam_dict["subject"], exam_dict["subject"][:3], "#3498db"))
                        subj_id = new_sid
            conn.execute("""
                         INSERT INTO exams (id, subject_id, subject, title, date, time, note, ignore_barrier, color)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                         """, (exam_dict["id"], subj_id, exam_dict["subject"], exam_dict["title"], exam_dict["date"],
                               exam_dict.get("time"), exam_dict.get("note", ""),
                               1 if exam_dict.get("ignore_barrier") else 0, exam_dict.get("color")))
            conn.commit()

    def update_exam(self, exam_dict):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE exams SET subject=?, title=?, date=?, time=?, note=?, ignore_barrier=?, color=? WHERE id = ?",
                (exam_dict["subject"], exam_dict["title"], exam_dict["date"], exam_dict.get("time"),
                 exam_dict.get("note", ""), 1 if exam_dict.get("ignore_barrier") else 0, exam_dict.get("color"),
                 exam_dict["id"]))
            conn.commit()

    def delete_exam(self, exam_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM exams WHERE id=?", (exam_id,))
            conn.commit()

    def get_topic(self, topic_id):
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM topics WHERE id=?", (topic_id,)).fetchone()
            if row:
                data = dict(row)
                data["locked"] = bool(data["locked"])
                return data
            return None

    def get_topics(self, exam_id=None):
        with self._get_conn() as conn:
            if exam_id: return [dict(r) for r in
                                conn.execute("SELECT * FROM topics WHERE exam_id=?", (exam_id,)).fetchall()]
            return [dict(r) for r in conn.execute("SELECT * FROM topics").fetchall()]

    def add_topic(self, topic_dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO topics (id, exam_id, name, status, scheduled_date, locked, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (topic_dict["id"], topic_dict["exam_id"], topic_dict["name"], topic_dict["status"],
                 topic_dict.get("scheduled_date"), 1 if topic_dict.get("locked") else 0, topic_dict.get("note", "")))
            conn.commit()

    def update_topic(self, topic_dict):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE topics SET exam_id=?, name=?, status=?, scheduled_date=?, locked=?, note=? WHERE id = ?",
                (topic_dict["exam_id"], topic_dict["name"], topic_dict["status"], topic_dict.get("scheduled_date"),
                 1 if topic_dict.get("locked") else 0, topic_dict.get("note", ""), topic_dict["id"]))
            conn.commit()

    # NOWOŚĆ: Bulk update dla SQL
    def update_topics_bulk(self, topics_list):
        with self._get_conn() as conn:
            for t in topics_list:
                conn.execute(
                    "UPDATE topics SET exam_id=?, name=?, status=?, scheduled_date=?, locked=?, note=? WHERE id = ?",
                    (t["exam_id"], t["name"], t["status"], t.get("scheduled_date"),
                     1 if t.get("locked") else 0, t.get("note", ""), t["id"])
                )
            conn.commit()

    def delete_topic(self, topic_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM topics WHERE id=?", (topic_id,))
            conn.commit()

    def get_task_lists(self):
        with self._get_conn() as conn: return [dict(r) for r in conn.execute("SELECT * FROM task_lists").fetchall()]

    def add_task_list(self, list_dict):
        with self._get_conn() as conn:
            conn.execute("INSERT INTO task_lists (id, name, icon) VALUES (?, ?, ?)",
                         (list_dict["id"], list_dict["name"], list_dict.get("icon", "")))
            conn.commit()

    def delete_task_list(self, list_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM task_lists WHERE id=?", (list_id,))
            conn.execute("DELETE FROM daily_tasks WHERE list_id=?", (list_id,))
            conn.commit()

    def get_daily_task(self, task_id):
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM daily_tasks WHERE id=?", (task_id,)).fetchone()
            return dict(row) if row else None

    def get_daily_tasks(self):
        with self._get_conn() as conn: return [dict(r) for r in conn.execute("SELECT * FROM daily_tasks").fetchall()]

    def add_daily_task(self, task_dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO daily_tasks (id, content, status, date, color, created_at, note, list_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (task_dict["id"], task_dict["content"], task_dict["status"], task_dict["date"], task_dict.get("color"),
                 task_dict.get("created_at"), task_dict.get("note", ""), task_dict.get("list_id")))
            conn.commit()

    def update_daily_task(self, task_dict):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE daily_tasks SET content=?, status=?, date=?, color=?, created_at=?, note=?, list_id=? WHERE id = ?",
                (task_dict["content"], task_dict["status"], task_dict["date"], task_dict.get("color"),
                 task_dict.get("created_at"), task_dict.get("note", ""), task_dict.get("list_id"), task_dict["id"]))
            conn.commit()

    def delete_daily_task(self, task_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM daily_tasks WHERE id=?", (task_id,))
            conn.commit()

    def get_blocked_dates(self):
        with self._get_conn() as conn: return [row["date"] for row in conn.execute("SELECT date FROM blocked_dates")]

    def add_blocked_date(self, date_str):
        with self._get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO blocked_dates (date) VALUES (?)", (date_str,))
            conn.commit()

    def remove_blocked_date(self, date_str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM blocked_dates WHERE date=?", (date_str,))
            conn.commit()

    def get_achievements(self):
        with self._get_conn() as conn: return [row["achievement_id"] for row in
                                               conn.execute("SELECT achievement_id FROM achievements")]

    def add_achievement(self, achievement_id):
        today = datetime.date.today().isoformat()
        with self._get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO achievements (achievement_id, date_earned) VALUES (?, ?)",
                         (achievement_id, today))
            conn.commit()

    def get_semesters(self):
        with self._get_conn() as conn: return [dict(r) for r in conn.execute("SELECT * FROM semesters").fetchall()]

    def add_semester(self, sem_dict):
        with self._get_conn() as conn:
            conn.execute("INSERT INTO semesters (id, name, start_date, end_date, is_current) VALUES (?, ?, ?, ?, ?)",
                         (sem_dict["id"], sem_dict["name"], sem_dict["start_date"], sem_dict["end_date"],
                          1 if sem_dict.get("is_current") else 0))
            conn.commit()

    def update_semester(self, sem_dict):
        with self._get_conn() as conn:
            conn.execute("UPDATE semesters SET name=?, start_date=?, end_date=?, is_current=? WHERE id=?",
                         (sem_dict["name"], sem_dict["start_date"], sem_dict["end_date"],
                          1 if sem_dict.get("is_current") else 0, sem_dict["id"]))
            conn.commit()

    def delete_semester(self, sem_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM semesters WHERE id=?", (sem_id,))
            conn.commit()

    def get_subjects(self, semester_id=None):
        with self._get_conn() as conn:
            if semester_id: return [dict(r) for r in conn.execute("SELECT * FROM subjects WHERE semester_id=?",
                                                                  (semester_id,)).fetchall()]
            return [dict(r) for r in conn.execute("SELECT * FROM subjects").fetchall()]

    def add_subject(self, sub_dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO subjects (id, semester_id, name, short_name, color, weight, start_datetime, end_datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (sub_dict["id"], sub_dict["semester_id"], sub_dict["name"], sub_dict["short_name"], sub_dict["color"],
                 sub_dict.get("weight", 1.0), sub_dict.get("start_datetime"), sub_dict.get("end_datetime")))
            conn.commit()

    def update_subject(self, sub_dict):
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE subjects SET semester_id=?, name=?, short_name=?, color=?, weight=?, start_datetime=?, end_datetime=? WHERE id=?",
                (sub_dict["semester_id"], sub_dict["name"], sub_dict["short_name"], sub_dict["color"],
                 sub_dict.get("weight", 1.0), sub_dict.get("start_datetime"), sub_dict.get("end_datetime"),
                 sub_dict["id"]))
            conn.commit()

    def delete_subject(self, sub_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM subjects WHERE id=?", (sub_id,))
            conn.commit()

    def get_schedule(self):
        with self._get_conn() as conn: return [dict(r) for r in
                                               conn.execute("SELECT * FROM schedule_entries").fetchall()]

    def get_schedule_entries_by_subject(self, subject_id):
        with self._get_conn() as conn: return [dict(r) for r in
                                               conn.execute("SELECT * FROM schedule_entries WHERE subject_id=?",
                                                            (subject_id,)).fetchall()]

    def add_schedule_entry(self, entry_dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO schedule_entries (id, subject_id, day_of_week, start_time, end_time, room, type, period_start, period_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entry_dict["id"], entry_dict["subject_id"], entry_dict["day_of_week"], entry_dict["start_time"],
                 entry_dict["end_time"], entry_dict.get("room"), entry_dict.get("type"), entry_dict.get("period_start"),
                 entry_dict.get("period_end")))
            conn.commit()

    def delete_schedule_entry(self, entry_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM schedule_entries WHERE id=?", (entry_id,))
            conn.commit()

    def add_schedule_cancellation(self, entry_id, date_str):
        new_id = f"cancel_{uuid.uuid4().hex[:8]}"
        with self._get_conn() as conn:
            conn.execute("INSERT INTO schedule_cancellations (id, entry_id, date) VALUES (?, ?, ?)",
                         (new_id, entry_id, date_str))
            conn.commit()

    def get_schedule_cancellations(self):
        with self._get_conn() as conn: return [dict(r) for r in conn.execute(
            "SELECT entry_id, date FROM schedule_cancellations").fetchall()]

    def get_grades(self, subject_id=None):
        with self._get_conn() as conn:
            if subject_id: return [dict(r) for r in
                                   conn.execute("SELECT * FROM grades WHERE subject_id=?", (subject_id,)).fetchall()]
            return [dict(r) for r in conn.execute("SELECT * FROM grades").fetchall()]

    def add_grade(self, grade_dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO grades (id, subject_id, module_id, value, weight, desc, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (grade_dict["id"], grade_dict["subject_id"], grade_dict.get("module_id"), grade_dict["value"],
                 grade_dict.get("weight", 1.0), grade_dict.get("desc"), grade_dict.get("date")))
            conn.commit()

    def delete_grade(self, grade_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM grades WHERE id=?", (grade_id,))
            conn.commit()

    def get_grade_modules(self, subject_id):
        with self._get_conn() as conn: return [dict(r) for r in
                                               conn.execute("SELECT * FROM grade_modules WHERE subject_id=?",
                                                            (subject_id,)).fetchall()]

    def add_grade_module(self, module_dict):
        with self._get_conn() as conn:
            conn.execute("INSERT INTO grade_modules (id, subject_id, name, weight) VALUES (?, ?, ?, ?)",
                         (module_dict["id"], module_dict["subject_id"], module_dict["name"], module_dict["weight"]))
            conn.commit()

    def update_grade_module(self, module_dict):
        with self._get_conn() as conn:
            conn.execute("UPDATE grade_modules SET name=?, weight=? WHERE id=?",
                         (module_dict["name"], module_dict["weight"], module_dict["id"]))
            conn.commit()

    def delete_grade_module(self, module_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM grade_modules WHERE id=?", (module_id,))
            conn.commit()

    def get_task_history(self):
        today = str(datetime.date.today())
        with self._get_conn() as conn:
            sql = "SELECT * FROM daily_tasks WHERE status = 'done' OR (date < ? AND status = 'todo') ORDER BY date DESC"
            return [dict(r) for r in conn.execute(sql, (today,)).fetchall()]

    def clear_task_history(self, today_str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM daily_tasks WHERE status = 'done' OR date < ?", (today_str,))
            conn.commit()

    def restore_overdue_tasks(self, today_str):
        with self._get_conn() as conn:
            count = conn.execute("SELECT count(*) FROM daily_tasks WHERE date < ? AND status = 'todo'",
                                 (today_str,)).fetchone()[0]
            if count > 0:
                conn.execute("UPDATE daily_tasks SET date = ? WHERE date < ? AND status = 'todo'",
                             (today_str, today_str))
                conn.commit()
            return count

    def get_event_lists(self):
        with self._get_conn() as conn: return [dict(r) for r in conn.execute("SELECT * FROM event_lists").fetchall()]

    def add_event_list(self, lst_dict):
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO event_lists (id, name, color) VALUES (?, ?, ?)",
                         (lst_dict["id"], lst_dict["name"], lst_dict.get("color", "#3498db")))
            conn.commit()

    def delete_event_list(self, lst_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM event_lists WHERE id=?", (lst_id,))
            conn.commit()

    def get_custom_events(self):
        with self._get_conn() as conn:
            res = []
            for r in conn.execute("SELECT * FROM custom_events").fetchall():
                d = dict(r)
                d["is_recurring"] = bool(d["is_recurring"])
                res.append(d)
            return res

    def add_custom_event(self, ev_dict):
        with self._get_conn() as conn:
            conn.execute("""INSERT OR REPLACE INTO custom_events 
                (id, list_id, title, is_recurring, date, day_of_week, start_time, end_time, start_date, end_date, color) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                         (ev_dict["id"], ev_dict.get("list_id"), ev_dict["title"],
                          1 if ev_dict.get("is_recurring") else 0, ev_dict.get("date"),
                          ev_dict.get("day_of_week"), ev_dict["start_time"], ev_dict["end_time"],
                          ev_dict.get("start_date"), ev_dict.get("end_date"), ev_dict.get("color", "#3498db")))
            conn.commit()

    def delete_custom_event(self, ev_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM custom_events WHERE id=?", (ev_id,))
            conn.commit()


# --- DOSTAWCA: CHMURA SUPABASE ---
class SupabaseProvider(BaseProvider):
    def __init__(self, url, key):
        if not SUPABASE_AVAILABLE:
            raise ImportError("Pakiet 'supabase' nie jest zainstalowany. Wykonaj: pip install supabase")
        self.client: Client = create_client(url, key)

    def _clean_dates(self, data):
        if isinstance(data, list):
            for item in data: self._clean_dates(item)
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str) and "T00:00" in value:
                    data[key] = value.split("T")[0]
        return data

    def get_settings(self):
        res = {}
        data = self.client.table("settings").select("*").execute().data
        for r in data:
            try:
                res[r["key"]] = json.loads(r["value"]) if isinstance(r["value"], str) else r["value"]
            except:
                res[r["key"]] = r["value"]
        defaults = DEFAULT_DATA["settings"].copy()
        for k, v in res.items():
            if k in defaults and isinstance(defaults[k], dict) and isinstance(v, dict):
                defaults[k].update(v)
            else:
                defaults[k] = v
        return defaults

    def update_setting(self, key, value):
        val = json.dumps(value) if isinstance(value, (dict, list)) else value
        self.client.table("settings").upsert({"key": key, "value": val}).execute()

    def get_global_stats(self):
        res = {}
        data = self.client.table("global_stats").select("*").execute().data
        for r in data:
            try:
                res[r["key"]] = json.loads(r["value"]) if isinstance(r["value"], str) else r["value"]
            except:
                res[r["key"]] = r["value"]
        defaults = DEFAULT_DATA["global_stats"].copy()
        defaults.update(res)
        return defaults

    def update_global_stat(self, key, value):
        val = json.dumps(value) if isinstance(value, (dict, list)) else value
        self.client.table("global_stats").upsert({"key": key, "value": val}).execute()

    def get_other_stats(self):
        res = {}
        data = self.client.table("stats").select("*").execute().data
        for r in data:
            try:
                res[r["key"]] = json.loads(r["value"]) if isinstance(r["value"], str) else r["value"]
            except:
                res[r["key"]] = r["value"]
        return res

    def update_other_stat(self, key, value):
        val = json.dumps(value) if isinstance(value, (dict, list)) else value
        self.client.table("stats").upsert({"key": key, "value": val}).execute()

    def get_custom_sounds(self):
        data = self.client.table("custom_sounds").select("*").execute().data
        for d in data:
            if "steps_json" in d:
                d["steps"] = json.loads(d["steps_json"]) if isinstance(d["steps_json"], str) else d["steps_json"]
                del d["steps_json"]
        return data

    def get_custom_sound(self, sound_id):
        data = self.client.table("custom_sounds").select("*").eq("id", sound_id).execute().data
        if data:
            d = data[0]
            if "steps_json" in d:
                d["steps"] = json.loads(d["steps_json"]) if isinstance(d["steps_json"], str) else d["steps_json"]
            return d
        return None

    def add_custom_sound(self, sound_dict):
        steps = json.dumps(sound_dict["steps"]) if isinstance(sound_dict["steps"], list) else sound_dict["steps"]
        self.client.table("custom_sounds").upsert(
            {"id": sound_dict["id"], "name": sound_dict["name"], "steps_json": steps}).execute()

    def delete_custom_sound(self, sound_id):
        self.client.table("custom_sounds").delete().eq("id", sound_id).execute()

    def _map_exam(self, e):
        e["ignore_barrier"] = bool(e.get("ignore_barrier", 0))
        if "subjects" in e and e["subjects"]:
            e["subject"] = e["subjects"].get("name", e.get("subject"))
            e["color"] = e["subjects"].get("color", e.get("color"))
        return e

    def get_exam(self, exam_id):
        data = self.client.table("exams").select("*, subjects(name, color)").eq("id", exam_id).execute().data
        return self._map_exam(self._clean_dates(data[0])) if data else None

    def get_exams(self):
        data = self.client.table("exams").select("*, subjects(name, color)").execute().data
        return [self._map_exam(self._clean_dates(e)) for e in data]

    def add_exam(self, exam_dict):
        payload = exam_dict.copy()
        payload["ignore_barrier"] = bool(payload.get("ignore_barrier"))
        if "color" not in payload: payload["color"] = None
        payload.pop("subject_name", None);
        payload.pop("subject_color", None);
        payload.pop("subjects", None)
        if not payload.get("subject_id") and payload.get("subject"):
            subj_data = self.client.table("subjects").select("id").eq("name", payload["subject"]).execute().data
            if subj_data: payload["subject_id"] = subj_data[0]["id"]
        self.client.table("exams").insert(payload).execute()

    def update_exam(self, exam_dict):
        payload = exam_dict.copy()
        payload.pop("id", None)
        payload["ignore_barrier"] = bool(payload.get("ignore_barrier"))
        payload.pop("subject_name", None);
        payload.pop("subject_color", None);
        payload.pop("subjects", None)
        self.client.table("exams").update(payload).eq("id", exam_dict["id"]).execute()

    def delete_exam(self, exam_id):
        self.client.table("exams").delete().eq("id", exam_id).execute()

    def get_topic(self, topic_id):
        data = self.client.table("topics").select("*").eq("id", topic_id).execute().data
        if data:
            d = data[0]
            d["locked"] = bool(d.get("locked", 0))
            return self._clean_dates(d)
        return None

    def get_topics(self, exam_id=None):
        query = self.client.table("topics").select("*")
        if exam_id: query = query.eq("exam_id", exam_id)
        data = query.execute().data
        for d in data: d["locked"] = bool(d.get("locked", 0))
        return self._clean_dates(data)

    def add_topic(self, topic_dict):
        payload = topic_dict.copy()
        payload["locked"] = bool(payload.get("locked"))
        self.client.table("topics").insert(payload).execute()

    def update_topic(self, topic_dict):
        payload = topic_dict.copy()
        payload.pop("id", None)
        payload["locked"] = bool(payload.get("locked"))
        self.client.table("topics").update(payload).eq("id", topic_dict["id"]).execute()

    # NOWOŚĆ: Bulk update dla Supabase (Upsert w jednym zapytaniu HTTP)
    def update_topics_bulk(self, topics_list):
        if not topics_list: return
        payloads = []
        for t in topics_list:
            p = t.copy()
            p["locked"] = bool(p.get("locked"))
            payloads.append(p)
        self.client.table("topics").upsert(payloads).execute()

    def delete_topic(self, topic_id):
        self.client.table("topics").delete().eq("id", topic_id).execute()

    def get_task_lists(self):
        return self.client.table("task_lists").select("*").execute().data

    def add_task_list(self, list_dict):
        self.client.table("task_lists").insert(list_dict).execute()

    def delete_task_list(self, list_id):
        self.client.table("task_lists").delete().eq("id", list_id).execute()
        self.client.table("daily_tasks").delete().eq("list_id", list_id).execute()

    def get_daily_task(self, task_id):
        data = self.client.table("daily_tasks").select("*").eq("id", task_id).execute().data
        return self._clean_dates(data[0]) if data else None

    def get_daily_tasks(self):
        data = self.client.table("daily_tasks").select("*").execute().data
        return self._clean_dates(data)

    def add_daily_task(self, task_dict):
        self.client.table("daily_tasks").insert(task_dict).execute()

    def update_daily_task(self, task_dict):
        payload = task_dict.copy()
        payload.pop("id", None)
        self.client.table("daily_tasks").update(payload).eq("id", task_dict["id"]).execute()

    def delete_daily_task(self, task_id):
        self.client.table("daily_tasks").delete().eq("id", task_id).execute()

    def get_blocked_dates(self):
        data = self.client.table("blocked_dates").select("date").execute().data
        return [self._clean_dates(d)["date"] for d in data]

    def add_blocked_date(self, date_str):
        self.client.table("blocked_dates").upsert({"date": date_str}).execute()

    def remove_blocked_date(self, date_str):
        self.client.table("blocked_dates").delete().eq("date", date_str).execute()

    def get_achievements(self):
        data = self.client.table("achievements").select("achievement_id").execute().data
        return [d["achievement_id"] for d in data]

    def add_achievement(self, achievement_id):
        today = datetime.date.today().isoformat()
        self.client.table("achievements").upsert({"achievement_id": achievement_id, "date_earned": today}).execute()

    def get_semesters(self):
        data = self.client.table("semesters").select("*").execute().data
        return self._clean_dates(data)

    def add_semester(self, sem_dict):
        payload = sem_dict.copy()
        payload["is_current"] = bool(payload.get("is_current"))
        self.client.table("semesters").insert(payload).execute()

    def update_semester(self, sem_dict):
        payload = sem_dict.copy()
        payload.pop("id", None)
        payload["is_current"] = bool(payload.get("is_current"))
        self.client.table("semesters").update(payload).eq("id", sem_dict["id"]).execute()

    def delete_semester(self, sem_id):
        self.client.table("semesters").delete().eq("id", sem_id).execute()

    def get_subjects(self, semester_id=None):
        query = self.client.table("subjects").select("*")
        if semester_id: query = query.eq("semester_id", semester_id)
        data = query.execute().data
        return self._clean_dates(data)

    def add_subject(self, sub_dict):
        self.client.table("subjects").insert(sub_dict).execute()

    def update_subject(self, sub_dict):
        payload = sub_dict.copy()
        payload.pop("id", None)
        self.client.table("subjects").update(payload).eq("id", sub_dict["id"]).execute()

    def delete_subject(self, sub_id):
        self.client.table("subjects").delete().eq("id", sub_id).execute()

    def get_schedule(self):
        data = self.client.table("schedule_entries").select("*").execute().data
        return self._clean_dates(data)

    def get_schedule_entries_by_subject(self, subject_id):
        data = self.client.table("schedule_entries").select("*").eq("subject_id", subject_id).execute().data
        return self._clean_dates(data)

    def add_schedule_entry(self, entry_dict):
        self.client.table("schedule_entries").insert(entry_dict).execute()

    def delete_schedule_entry(self, entry_id):
        self.client.table("schedule_entries").delete().eq("id", entry_id).execute()

    def add_schedule_cancellation(self, entry_id, date_str):
        new_id = f"cancel_{uuid.uuid4().hex[:8]}"
        self.client.table("schedule_cancellations").insert(
            {"id": new_id, "entry_id": entry_id, "date": date_str}).execute()

    def get_schedule_cancellations(self):
        data = self.client.table("schedule_cancellations").select("entry_id, date").execute().data
        return self._clean_dates(data)

    def get_grades(self, subject_id=None):
        query = self.client.table("grades").select("*")
        if subject_id: query = query.eq("subject_id", subject_id)
        data = query.execute().data
        for d in data:
            if "desc_text" in d: d["desc"] = d.pop("desc_text")
        return self._clean_dates(data)

    def add_grade(self, grade_dict):
        payload = grade_dict.copy()
        if "desc" in payload: payload["desc_text"] = payload.pop("desc")
        self.client.table("grades").insert(payload).execute()

    def delete_grade(self, grade_id):
        self.client.table("grades").delete().eq("id", grade_id).execute()

    def get_grade_modules(self, subject_id):
        data = self.client.table("grade_modules").select("*").eq("subject_id", subject_id).execute().data
        return self._clean_dates(data)

    def add_grade_module(self, module_dict):
        self.client.table("grade_modules").insert(module_dict).execute()

    def update_grade_module(self, module_dict):
        payload = module_dict.copy()
        payload.pop("id", None)
        self.client.table("grade_modules").update(payload).eq("id", module_dict["id"]).execute()

    def delete_grade_module(self, module_id):
        self.client.table("grade_modules").delete().eq("id", module_id).execute()

    def get_task_history(self):
        today = str(datetime.date.today())
        query = self.client.table("daily_tasks").select("*").or_(
            f"status.eq.done,and(date.lt.{today},status.eq.todo)").order("date", desc=True)
        data = query.execute().data
        return self._clean_dates(data)

    def clear_task_history(self, today_str):
        to_delete = self.client.table("daily_tasks").select("id").or_(
            f"status.eq.done,date.lt.{today_str}").execute().data
        ids = [t["id"] for t in to_delete]
        if ids: self.client.table("daily_tasks").delete().in_("id", ids).execute()

    def restore_overdue_tasks(self, today_str):
        tasks = self.client.table("daily_tasks").select("id").lt("date", today_str).eq("status", "todo").execute().data
        count = len(tasks)
        if count > 0:
            ids = [t["id"] for t in tasks]
            self.client.table("daily_tasks").update({"date": today_str}).in_("id", ids).execute()
        return count

    def get_event_lists(self):
        data = self.client.table("event_lists").select("*").execute().data
        return self._clean_dates(data)

    def add_event_list(self, lst_dict):
        self.client.table("event_lists").upsert(lst_dict).execute()

    def delete_event_list(self, lst_id):
        self.client.table("event_lists").delete().eq("id", lst_id).execute()

    def get_custom_events(self):
        data = self.client.table("custom_events").select("*").execute().data
        return self._clean_dates(data)

    def add_custom_event(self, ev_dict):
        payload = ev_dict.copy()
        payload["is_recurring"] = bool(payload.get("is_recurring"))
        self.client.table("custom_events").upsert(payload).execute()

    def delete_custom_event(self, ev_id):
        self.client.table("custom_events").delete().eq("id", ev_id).execute()

# --- CONFIG LOADER ---
def load_config():
    # Ścieżka do pliku SQL w tym samym folderze co config
    SQL_PATH = CONFIG_PATH.parent / "schema.sql"

    # Zawsze twórz/aktualizuj plik SQL, żeby użytkownik go widział
    try:
        SQL_PATH.write_text(SQL_SCHEMA.strip(), encoding="utf-8")
    except Exception as e:
        print(f"Could not create schema.sql: {e}")

    default_config = {
        "db_mode": "local",
        "supabase_url": "",
        "supabase_key": "",
        "cloud_onboarding_shown": False
    }

    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(default_config, indent=4), encoding="utf-8")
        return default_config
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return default_config


class StorageManager:
    def __init__(self, db_path):
        self.config = load_config()
        self.mode = self.config.get("db_mode", "local")
        self.local = SQLiteProvider(db_path)
        self.cloud = None

        if self.mode == "cloud":
            url = self.config.get("supabase_url")
            key = self.config.get("supabase_key")
            if url and key:
                try:
                    self.cloud = SupabaseProvider(url, key)
                except Exception as e:
                    print(f"[Storage] Cloud init error: {e}")

    def mark_onboarding_done(self):
        self.config["cloud_onboarding_shown"] = True
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def perform_cloud_migration(self, progress_callback=None):
        from core.migration import DataMigrator

        # Pobieramy najnowsze dane z configu
        url = self.config.get("supabase_url")
        key = self.config.get("supabase_key")

        migrator = DataMigrator(self.local, url, key)
        success, message = migrator.run(progress_callback)

        if success:
            # Automatycznie przełączamy na chmurę po sukcesie
            self.config["db_mode"] = "cloud"
            self.mark_onboarding_done()  # Ta metoda którą dodaliśmy wcześniej

        return success, message

    def sync_down(self, status_callback=None):
        if not self.cloud: return

        def update(text):
            if status_callback:
                status_callback(text)
            else:
                print(f"[Storage] {text}")

        try:
            update("Connecting to the cloud...")
            settings = self.cloud.get_settings()
            update("Downloading tasks...")
            tasks = self.cloud.get_daily_tasks()
            update("Downloading the schedule...")
            semesters = self.cloud.get_semesters()
            subjects = self.cloud.get_subjects()
            update("Downloading exams...")
            exams = self.cloud.get_exams()
            topics = self.cloud.get_topics()
            update("Downloading lists...")
            lists = self.cloud.get_task_lists()
            event_lists = self.cloud.get_event_lists() if hasattr(self.cloud, 'get_event_lists') else []
            custom_events = self.cloud.get_custom_events() if hasattr(self.cloud, 'get_custom_events') else []
            update("Downloading statistics and achievements...")
            global_stats = self.cloud.get_global_stats()
            other_stats = self.cloud.get_other_stats()
            achievements = self.cloud.get_achievements()
            update("Downloading the calendar and sounds...")
            blocked_dates = self.cloud.get_blocked_dates()
            custom_sounds = self.cloud.get_custom_sounds()
            schedule = self.cloud.get_schedule()
            cancellations = self.cloud.get_schedule_cancellations()
            update("Downloading grades...")
            grades = self.cloud.get_grades()
            # Pobieramy wszystkie moduły bezpośrednio, bo Twoja metoda wymagała subject_id
            grade_modules = self.cloud.client.table("grade_modules").select("*").execute().data

            update("Saving data locally...")
            with self.local._get_conn() as conn:
                conn.execute("PRAGMA foreign_keys = OFF;")
                for k, v in settings.items(): conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                                                           (k, json.dumps(v)))
                conn.execute("DELETE FROM daily_tasks")
                for t in tasks: conn.execute(
                    "INSERT INTO daily_tasks (id, content, status, date, color, created_at, note, list_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (t['id'], t['content'], t['status'], t['date'], t.get('color'), t.get('created_at'), t.get('note'),
                     t.get('list_id')))
                conn.execute("DELETE FROM semesters")
                for s in semesters: conn.execute(
                    "INSERT INTO semesters (id, name, start_date, end_date, is_current) VALUES (?, ?, ?, ?, ?)",
                    (s['id'], s['name'], s['start_date'], s['end_date'], 1 if s.get('is_current') else 0))
                conn.execute("DELETE FROM subjects")
                for sub in subjects: conn.execute(
                    "INSERT INTO subjects (id, semester_id, name, short_name, color, weight, start_datetime, end_datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (sub['id'], sub['semester_id'], sub['name'], sub['short_name'], sub['color'],
                     sub.get('weight', 1.0), sub.get('start_datetime'), sub.get('end_datetime')))
                conn.execute("DELETE FROM exams")
                for ex in exams: conn.execute(
                    "INSERT INTO exams (id, subject_id, subject, title, date, time, note, ignore_barrier, color) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (ex['id'], ex.get('subject_id'), ex.get('subject'), ex['title'], ex['date'], ex.get('time'),
                     ex.get('note'), 1 if ex.get('ignore_barrier') else 0, ex.get('color')))
                conn.execute("DELETE FROM topics")
                for tp in topics: conn.execute(
                    "INSERT INTO topics (id, exam_id, name, status, scheduled_date, locked, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (tp['id'], tp['exam_id'], tp['name'], tp['status'], tp.get('scheduled_date'),
                     1 if tp.get('locked') else 0, tp.get('note')))
                conn.execute("DELETE FROM task_lists")
                for lst in lists: conn.execute("INSERT INTO task_lists (id, name, icon) VALUES (?, ?, ?)",
                                               (lst['id'], lst['name'], lst.get('icon')))
                # Statystyki (Zastępujemy tylko pobrane klucze)
                for k, v in global_stats.items():
                    conn.execute("INSERT OR REPLACE INTO global_stats (key, value) VALUES (?, ?)", (k, json.dumps(v)))
                for k, v in other_stats.items():
                    conn.execute("INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (k, json.dumps(v)))

                # Dźwięki
                conn.execute("DELETE FROM custom_sounds")
                for s in custom_sounds:
                    steps_json = json.dumps(s.get('steps', []))
                    conn.execute("INSERT INTO custom_sounds (id, name, steps_json) VALUES (?, ?, ?)",
                                 (s['id'], s['name'], steps_json))

                # Zablokowane daty
                conn.execute("DELETE FROM blocked_dates")
                for bd in blocked_dates:
                    conn.execute("INSERT INTO blocked_dates (date) VALUES (?)", (bd,))

                # Osiągnięcia
                conn.execute("DELETE FROM achievements")
                today_str = datetime.date.today().isoformat()
                for ach_id in achievements:
                    conn.execute("INSERT INTO achievements (achievement_id, date_earned) VALUES (?, ?)",
                                 (ach_id, today_str))

                # Harmonogram
                conn.execute("DELETE FROM schedule_entries")
                for se in schedule:
                    conn.execute(
                        "INSERT INTO schedule_entries (id, subject_id, day_of_week, start_time, end_time, room, type, period_start, period_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (se['id'], se.get('subject_id'), se['day_of_week'], se['start_time'], se['end_time'],
                         se.get('room'), se.get('type'), se.get('period_start'), se.get('period_end')))

                # Anulowane zajęcia
                conn.execute("DELETE FROM schedule_cancellations")
                for sc in cancellations:
                    sc_id = f"cancel_{uuid.uuid4().hex[:8]}"  # Generujemy lokalne ID
                    conn.execute("INSERT INTO schedule_cancellations (id, entry_id, date) VALUES (?, ?, ?)",
                                 (sc_id, sc['entry_id'], sc['date']))

                # Oceny i moduły
                conn.execute("DELETE FROM grade_modules")
                for gm in grade_modules:
                    conn.execute("INSERT INTO grade_modules (id, subject_id, name, weight) VALUES (?, ?, ?, ?)",
                                 (gm['id'], gm['subject_id'], gm['name'], gm.get('weight', 0.0)))

                conn.execute("DELETE FROM grades")
                for g in grades:
                    conn.execute(
                        "INSERT INTO grades (id, subject_id, module_id, value, weight, desc, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (g['id'], g['subject_id'], g.get('module_id'), g['value'], g.get('weight', 1.0), g.get('desc'),
                         g.get('date')))

                conn.execute("DELETE FROM event_lists")
                for el in event_lists:
                    conn.execute("INSERT INTO event_lists (id, name, color) VALUES (?, ?, ?)",
                                 (el['id'], el['name'], el.get('color')))

                conn.execute("DELETE FROM custom_events")
                for ce in custom_events:
                    conn.execute("""INSERT INTO custom_events
                                    (id, list_id, title, is_recurring, date, day_of_week, start_time, end_time,
                                     start_date, end_date, color)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                 (ce['id'], ce.get('list_id'), ce['title'], 1 if ce.get('is_recurring') else 0,
                                  ce.get('date'),
                                  ce.get('day_of_week'), ce['start_time'], ce['end_time'], ce.get('start_date'),
                                  ce.get('end_date'), ce.get('color')))
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.commit()
            update("Ready!")
        except Exception as e:
            update(f"Error: {e}")
            print(f"[Storage] Critical Err..: {e}")

    def _bg_cloud_sync(self, method_name, *args, **kwargs):
        if self.cloud and hasattr(self.cloud, method_name):
            def run():
                import time
                for _ in range(3):
                    try:
                        getattr(self.cloud, method_name)(*args, **kwargs)
                        break
                    except Exception as e:
                        if "35" in str(e):
                            time.sleep(0.3)
                        else:
                            print(f"[Supabase Sync Error in {method_name}]: {e}")
                            break

            threading.Thread(target=run, daemon=True).start()

    def _sanitize_nulls(self, data):
        if isinstance(data, list):
            for item in data: self._sanitize_nulls(item)
        elif isinstance(data, dict):
            for k, v in data.items():
                if v is None and k in ["note", "time", "content", "desc", "room", "type", "name", "title", "subject",
                                       "short_name"]:
                    data[k] = ""
        return data

    def get_settings(self):
        return self.local.get_settings()

    def get_global_stats(self):
        return self.local.get_global_stats()

    def get_other_stats(self):
        return self.local.get_other_stats()

    def get_custom_sounds(self):
        return self.local.get_custom_sounds()

    def get_custom_sound(self, sound_id):
        return self.local.get_custom_sound(sound_id)

    def get_exam(self, exam_id):
        return self._sanitize_nulls(self.local.get_exam(exam_id))

    def get_exams(self):
        return self._sanitize_nulls(self.local.get_exams())

    def get_topic(self, topic_id):
        return self._sanitize_nulls(self.local.get_topic(topic_id))

    def get_topics(self, exam_id=None):
        return self._sanitize_nulls(self.local.get_topics(exam_id))

    def get_task_lists(self):
        return self._sanitize_nulls(self.local.get_task_lists())

    def get_daily_task(self, task_id):
        return self._sanitize_nulls(self.local.get_daily_task(task_id))

    def get_daily_tasks(self):
        return self._sanitize_nulls(self.local.get_daily_tasks())

    def get_blocked_dates(self):
        return self.local.get_blocked_dates()

    def get_achievements(self):
        return self.local.get_achievements()

    def get_semesters(self):
        return self._sanitize_nulls(self.local.get_semesters())

    def get_subjects(self, semester_id=None):
        return self._sanitize_nulls(self.local.get_subjects(semester_id))

    def get_schedule(self):
        return self._sanitize_nulls(self.local.get_schedule())

    def get_schedule_entries_by_subject(self, subject_id):
        return self._sanitize_nulls(self.local.get_schedule_entries_by_subject(subject_id))

    def get_schedule_cancellations(self):
        return self.local.get_schedule_cancellations()

    def get_grades(self, subject_id=None):
        return self._sanitize_nulls(self.local.get_grades(subject_id))

    def get_grade_modules(self, subject_id):
        return self._sanitize_nulls(self.local.get_grade_modules(subject_id))

    def get_task_history(self):
        return self._sanitize_nulls(self.local.get_task_history())

    def update_setting(self, key, value):
        self.local.update_setting(key, value); self._bg_cloud_sync("update_setting", key, value)

    def update_global_stat(self, key, value):
        self.local.update_global_stat(key, value); self._bg_cloud_sync("update_global_stat", key, value)

    def update_other_stat(self, key, value):
        self.local.update_other_stat(key, value); self._bg_cloud_sync("update_other_stat", key, value)

    def add_custom_sound(self, sound_dict):
        self.local.add_custom_sound(sound_dict); self._bg_cloud_sync("add_custom_sound", sound_dict)

    def delete_custom_sound(self, sound_id):
        self.local.delete_custom_sound(sound_id); self._bg_cloud_sync("delete_custom_sound", sound_id)

    def add_exam(self, exam_dict):
        self.local.add_exam(exam_dict); self._bg_cloud_sync("add_exam", exam_dict)

    def update_exam(self, exam_dict):
        self.local.update_exam(exam_dict); self._bg_cloud_sync("update_exam", exam_dict)

    def delete_exam(self, exam_id):
        self.local.delete_exam(exam_id); self._bg_cloud_sync("delete_exam", exam_id)

    def add_topic(self, topic_dict):
        self.local.add_topic(topic_dict); self._bg_cloud_sync("add_topic", topic_dict)

    def update_topic(self, topic_dict):
        self.local.update_topic(topic_dict); self._bg_cloud_sync("update_topic", topic_dict)

    # NOWOŚĆ: Przekierowanie do hurtowej aktualizacji tematów
    def update_topics_bulk(self, topics_list):
        self.local.update_topics_bulk(topics_list)
        self._bg_cloud_sync("update_topics_bulk", topics_list)

    def delete_topic(self, topic_id):
        self.local.delete_topic(topic_id); self._bg_cloud_sync("delete_topic", topic_id)

    def add_task_list(self, list_dict):
        self.local.add_task_list(list_dict); self._bg_cloud_sync("add_task_list", list_dict)

    def delete_task_list(self, list_id):
        self.local.delete_task_list(list_id); self._bg_cloud_sync("delete_task_list", list_id)

    def add_daily_task(self, task_dict):
        self.local.add_daily_task(task_dict); self._bg_cloud_sync("add_daily_task", task_dict)

    def update_daily_task(self, task_dict):
        self.local.update_daily_task(task_dict); self._bg_cloud_sync("update_daily_task", task_dict)

    def delete_daily_task(self, task_id):
        self.local.delete_daily_task(task_id); self._bg_cloud_sync("delete_daily_task", task_id)

    def add_blocked_date(self, date_str):
        self.local.add_blocked_date(date_str); self._bg_cloud_sync("add_blocked_date", date_str)

    def remove_blocked_date(self, date_str):
        self.local.remove_blocked_date(date_str); self._bg_cloud_sync("remove_blocked_date", date_str)

    def add_achievement(self, achievement_id):
        self.local.add_achievement(achievement_id); self._bg_cloud_sync("add_achievement", achievement_id)

    def add_semester(self, sem_dict):
        self.local.add_semester(sem_dict); self._bg_cloud_sync("add_semester", sem_dict)

    def update_semester(self, sem_dict):
        self.local.update_semester(sem_dict); self._bg_cloud_sync("update_semester", sem_dict)

    def delete_semester(self, sem_id):
        self.local.delete_semester(sem_id); self._bg_cloud_sync("delete_semester", sem_id)

    def add_subject(self, sub_dict):
        self.local.add_subject(sub_dict); self._bg_cloud_sync("add_subject", sub_dict)

    def update_subject(self, sub_dict):
        self.local.update_subject(sub_dict); self._bg_cloud_sync("update_subject", sub_dict)

    def delete_subject(self, sub_id):
        self.local.delete_subject(sub_id); self._bg_cloud_sync("delete_subject", sub_id)

    def add_schedule_entry(self, entry_dict):
        self.local.add_schedule_entry(entry_dict); self._bg_cloud_sync("add_schedule_entry", entry_dict)

    def delete_schedule_entry(self, entry_id):
        self.local.delete_schedule_entry(entry_id); self._bg_cloud_sync("delete_schedule_entry", entry_id)

    def add_schedule_cancellation(self, entry_id, date_str):
        self.local.add_schedule_cancellation(entry_id, date_str); self._bg_cloud_sync("add_schedule_cancellation",
                                                                                      entry_id, date_str)

    def add_grade(self, grade_dict):
        self.local.add_grade(grade_dict); self._bg_cloud_sync("add_grade", grade_dict)

    def delete_grade(self, grade_id):
        self.local.delete_grade(grade_id); self._bg_cloud_sync("delete_grade", grade_id)

    def add_grade_module(self, module_dict):
        self.local.add_grade_module(module_dict); self._bg_cloud_sync("add_grade_module", module_dict)

    def update_grade_module(self, module_dict):
        self.local.update_grade_module(module_dict); self._bg_cloud_sync("update_grade_module", module_dict)

    def delete_grade_module(self, module_id):
        self.local.delete_grade_module(module_id); self._bg_cloud_sync("delete_grade_module", module_id)

    def clear_task_history(self, today_str):
        self.local.clear_task_history(today_str); self._bg_cloud_sync("clear_task_history", today_str)

    def restore_overdue_tasks(self, today_str):
        res = self.local.restore_overdue_tasks(today_str)
        if res > 0:
            for t in self.local.get_daily_tasks(): self._bg_cloud_sync("update_daily_task", t)
        return res

    def get_event_lists(self):
        return self._sanitize_nulls(self.local.get_event_lists())

    def get_custom_events(self):
        return self._sanitize_nulls(self.local.get_custom_events())

    def add_event_list(self, lst_dict):
        self.local.add_event_list(lst_dict);
        self._bg_cloud_sync("add_event_list", lst_dict)

    def delete_event_list(self, lst_id):
        self.local.delete_event_list(lst_id);
        self._bg_cloud_sync("delete_event_list", lst_id)

    def add_custom_event(self, ev_dict):
        self.local.add_custom_event(ev_dict);
        self._bg_cloud_sync("add_custom_event", ev_dict)

    def delete_custom_event(self, ev_id):
        self.local.delete_custom_event(ev_id);
        self._bg_cloud_sync("delete_custom_event", ev_id)


manager = StorageManager(DB_PATH)


def load_language(lang_code="en"):
    file_path = LANG_DIR / f"lang_{lang_code}.json"
    if file_path.exists(): return json.loads(file_path.read_text(encoding="utf-8"))
    alternative_path = LANG_DIR / "lang_en.json"
    if alternative_path.exists(): return json.loads(alternative_path.read_text(encoding="utf-8"))
    return {}