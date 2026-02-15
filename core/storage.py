import json
import sqlite3
import datetime
import uuid
from pathlib import Path
import platformdirs

# --- KONFIGURACJA ---
# False: folder projektu/core | True: folder systemowy (AppData/Config)
USE_SYSTEM_STORAGE = True

# Nazwy aplikacji
APP_NAME = "StudyPlanner"
APP_AUTHOR = "Meimox"

# Ścieżki
CORE_DIR = Path(__file__).resolve().parent
LOCAL_DB_PATH = CORE_DIR / "storage.db"
LOCAL_JSON_PATH = CORE_DIR / "storage.json"  # Potrzebne do migracji

SYSTEM_DIR = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
SYSTEM_DB_PATH = SYSTEM_DIR / "storage.db"
SYSTEM_JSON_PATH = SYSTEM_DIR / "storage.json"  # Potrzebne do migracji

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
        "badge_mode": "default",

        # --- NOWE USTAWIENIA HARMONOGRAMU ---
        "schedule_use_full_name": False,  # False = Skrócona, True = Pełna
        "schedule_show_times": False,  # Czy pokazywać np. 08:00 - 09:30 w kafelku
        "schedule_show_room": True,  # Czy pokazywać salę

        # NOWE USTAWIENIA OCEN
        "grading_system": {
            "grade_mode": "percentage",  # "numeric" (2-5) lub "percentage" (0-100)
            "weight_mode": "percentage",  # "numeric" (1-5) lub "percentage" (0-100)
            "pass_threshold": 50
        },
        # NOWE: Domyślne przypisania dźwięków (ID dźwięku lub None)
        "sound_timer_finish": "def_level_up",  # Domyślnie Level Up
        "sound_achievement": "def_coin",  # Domyślnie Coin
        "sound_all_done": "def_fanfare",  # Domyślnie Fanfare
        # NOWE: GŁOŚNOŚĆ I WYCISZENIE
        "sound_enabled": True,
        "sound_volume": 0.5
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

# --- DOMYŚLNE DŹWIĘKI (PRESETY) ---
DEFAULT_SOUNDS = [
    {
        "id": "def_coin",
        "name": "Retro Coin",
        "steps": [
            {"freq": 988, "dur": 0.08, "type": "Square"},  # B5
            {"freq": 1319, "dur": 0.35, "type": "Square"}  # E6
        ]
    },
    {
        "id": "def_level_up",
        "name": "Level Up!",
        "steps": [
            {"freq": 523, "dur": 0.1, "type": "Square"},  # C5
            {"freq": 659, "dur": 0.1, "type": "Square"},  # E5
            {"freq": 784, "dur": 0.1, "type": "Square"},  # G5
            {"freq": 1046, "dur": 0.1, "type": "Square"},  # C6
            {"freq": 784, "dur": 0.1, "type": "Square"},  # G5
            {"freq": 1046, "dur": 0.4, "type": "Square"}  # C6
        ]
    },
    {
        "id": "def_game_over",
        "name": "Game Over",
        "steps": [
            {"freq": 784, "dur": 0.3, "type": "Sawtooth"},  # G5
            {"freq": 740, "dur": 0.3, "type": "Sawtooth"},  # F#5
            {"freq": 698, "dur": 0.3, "type": "Sawtooth"},  # F5
            {"freq": 622, "dur": 0.8, "type": "Sawtooth"}  # D#5
        ]
    },
    {
        "id": "def_laser",
        "name": "Laser Shoot",
        "steps": [
            {"freq": 1200, "dur": 0.05, "type": "Sawtooth"},
            {"freq": 800, "dur": 0.05, "type": "Sawtooth"},
            {"freq": 400, "dur": 0.05, "type": "Sawtooth"},
            {"freq": 200, "dur": 0.05, "type": "Sawtooth"}
        ]
    },
    {
        "id": "def_alarm",
        "name": "Red Alert",
        "steps": [
            {"freq": 880, "dur": 0.3, "type": "Square"},
            {"freq": 440, "dur": 0.3, "type": "Square"},
            {"freq": 880, "dur": 0.3, "type": "Square"},
            {"freq": 440, "dur": 0.3, "type": "Square"}
        ]
    },
    {
        "id": "def_magic",
        "name": "Magic Spell",
        "steps": [
            {"freq": 1000, "dur": 0.1, "type": "Sine"},
            {"freq": 1500, "dur": 0.1, "type": "Sine"},
            {"freq": 2000, "dur": 0.1, "type": "Sine"},
            {"freq": 2500, "dur": 0.4, "type": "Sine"}
        ]
    },
    {
        "id": "def_fanfare",
        "name": "Victory Fanfare",
        "steps": [
            {"freq": 523, "dur": 0.15, "type": "Square"},  # C5
            {"freq": 659, "dur": 0.15, "type": "Square"},  # E5
            {"freq": 784, "dur": 0.15, "type": "Square"},  # G5
            {"freq": 1046, "dur": 0.6, "type": "Square"}  # C6
        ]
    }
]


class StorageManager:
    def __init__(self, db_path):
        """
        Inicjalizuje managera, tworzy strukturę bazy danych i sprawdza
        czy wymagana jest migracja ze starego formatu JSON.
        """
        self.db_path = db_path
        self._init_db()
        self._check_migrations()
        self._ensure_default_sounds()  # Dodanie domyślnych dźwięków

    def _get_conn(self):
        """Pomocnicza funkcja zwracająca połączenie z row_factory (używać wewnątrz with)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")  # Włączamy klucze obce
        return conn

    def _init_db(self):
        """Tworzy strukturę tabel, jeśli nie istnieją."""
        with self._get_conn() as conn:
            # --- TABELE PODSTAWOWE (STARY SCHEMAT) ---

            # Tabela EXAMS
            conn.execute("""
                CREATE TABLE IF NOT EXISTS exams (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT, -- Nowa kolumna (FK)
                    subject TEXT, -- Stara kolumna (Legacy tekst)
                    title TEXT,
                    date TEXT,
                    time TEXT, -- Nowa kolumna: Godzina egzaminu
                    note TEXT,
                    ignore_barrier INTEGER DEFAULT 0,
                    color TEXT,
                    FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE SET NULL
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
                         CREATE TABLE IF NOT EXISTS daily_tasks
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
                             TEXT
                         )
                         """)

            try:
                conn.execute("ALTER TABLE daily_tasks ADD COLUMN note TEXT")
            except sqlite3.OperationalError:
                pass  # Kolumna już istnieje

            conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS global_stats (key TEXT PRIMARY KEY, value TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS blocked_dates (date TEXT PRIMARY KEY)")
            conn.execute("CREATE TABLE IF NOT EXISTS achievements (achievement_id TEXT PRIMARY KEY, date_earned TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value TEXT)")

            # --- NOWE TABELE (RELACYJNE v2) ---

            # 1. SEMESTRY
            conn.execute("""
                CREATE TABLE IF NOT EXISTS semesters (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    is_current INTEGER DEFAULT 0
                )
            """)

            # 2. PRZEDMIOTY (SUBJECTS)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id TEXT PRIMARY KEY,
                    semester_id TEXT,
                    name TEXT,
                    short_name TEXT,
                    color TEXT,
                    weight REAL DEFAULT 1.0,
                    start_datetime TEXT,
                    end_datetime TEXT,
                    FOREIGN KEY (semester_id) REFERENCES semesters (id) ON DELETE CASCADE
                )
            """)

            # 3. PLAN ZAJĘĆ (SCHEDULE)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schedule_entries (
                    id TEXT PRIMARY KEY,
                    subject_id TEXT,
                    day_of_week INTEGER,
                    start_time TEXT,
                    end_time TEXT,
                    room TEXT,
                    type TEXT,
                    period_start TEXT,
                    period_end TEXT,
                    FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
                )
            """)

            # 3b. ODWOŁANE ZAJĘCIA (EXCEPTIONS) - NOWOŚĆ
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schedule_cancellations (
                    id TEXT PRIMARY KEY,
                    entry_id TEXT,
                    date TEXT, -- Data konkretnego dnia (YYYY-MM-DD), w którym zajęcia są odwołane
                    FOREIGN KEY (entry_id) REFERENCES schedule_entries (id) ON DELETE CASCADE
                )
                         """)

            # 4. OCENY (GRADES)
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS grades
                         (
                             id TEXT PRIMARY KEY,
                             subject_id TEXT,
                             module_id TEXT,
                             value REAL,
                             weight REAL DEFAULT 1.0,
                             desc TEXT,
                             date TEXT,
                             FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE,
                             FOREIGN KEY (module_id) REFERENCES grade_modules (id) ON DELETE SET NULL
                         )
                         """)

            # 5. MODUŁY OCEN
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS grade_modules
                         (
                             id TEXT PRIMARY KEY,
                             subject_id TEXT,
                             name TEXT,
                             weight REAL DEFAULT 0.0,
                             FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
                         )
                         """)

            # 6. NIESTANDARDOWE DŹWIĘKI (RETRO AUDIO LAB)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_sounds (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    steps_json TEXT -- Przechowuje listę kroków (freq, dur, type) jako JSON
                )
            """)

            try:
                conn.execute(
                    "ALTER TABLE grades ADD COLUMN module_id TEXT REFERENCES grade_modules(id) ON DELETE SET NULL")
            except sqlite3.OperationalError:
                pass  # Kolumna już istnieje

    def _ensure_default_sounds(self):
        """Dodaje domyślne dźwięki do bazy, jeśli ich nie ma."""
        with self._get_conn() as conn:
            for sound in DEFAULT_SOUNDS:
                # Sprawdź czy dźwięk o tym ID już istnieje
                exists = conn.execute("SELECT 1 FROM custom_sounds WHERE id=?", (sound["id"],)).fetchone()
                if not exists:
                    steps_json = json.dumps(sound["steps"])
                    conn.execute("INSERT INTO custom_sounds (id, name, steps_json) VALUES (?, ?, ?)",
                                 (sound["id"], sound["name"], steps_json))
            conn.commit()

    # --- MIGRACJE ---

    def _check_migrations(self):
        """Zarządza migracjami: JSON -> SQL v1 oraz SQL v1 -> SQL v2 (Relacyjne)."""

        # 1. Migracja z JSON (Legacy)
        should_migrate_json = False
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT count(*) FROM exams")
            if cursor.fetchone()[0] == 0:
                cursor = conn.execute("SELECT count(*) FROM settings")
                if cursor.fetchone()[0] == 0:
                    should_migrate_json = True

        if should_migrate_json and OLD_JSON_PATH.exists():
            self._migrate_json_to_sql()

        # 2. Migracja Relacyjna
        self._migrate_to_relational_schema()

        # 3. Migracja Przedmiotów (Dodanie kolumn czasowych)
        self._migrate_subjects_add_dates()

        # 4. Migracja Egzaminów (Dodanie godziny)
        self._migrate_exams_add_time()

    def _migrate_json_to_sql(self):
        """Stara migracja z JSON (bez zmian logicznych)."""
        try:
            print(f"[Storage] Rozpoczynam migrację z {OLD_JSON_PATH}...")
            data = json.loads(OLD_JSON_PATH.read_text(encoding="utf-8"))
            today_str = datetime.date.today().isoformat()

            with self._get_conn() as conn:
                if "settings" in data:
                    for k, v in data["settings"].items():
                        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, json.dumps(v)))
                if "global_stats" in data:
                    for k, v in data["global_stats"].items():
                        conn.execute("INSERT OR REPLACE INTO global_stats (key, value) VALUES (?, ?)",
                                     (k, json.dumps(v)))
                if "stats" in data:
                    for k, v in data["stats"].items():
                        conn.execute("INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (k, json.dumps(v)))
                if "exams" in data:
                    for e in data["exams"]:
                        conn.execute(
                            "INSERT INTO exams (id, subject, title, date, note, ignore_barrier, color) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (e.get("id"), e.get("subject"), e.get("title"), e.get("date"), e.get("note", ""),
                             1 if e.get("ignore_barrier") else 0, e.get("color")))
                if "topics" in data:
                    for t in data["topics"]:
                        conn.execute(
                            "INSERT INTO topics (id, exam_id, name, status, scheduled_date, locked, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (t.get("id"), t.get("exam_id"), t.get("name"), t.get("status"), t.get("scheduled_date"),
                             1 if t.get("locked") else 0, t.get("note", "")))
                if "daily_tasks" in data:
                    for dt in data["daily_tasks"]:
                        conn.execute(
                            "INSERT INTO daily_tasks (id, content, status, date, color, created_at, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (dt.get("id"), dt.get("content"), dt.get("status"), dt.get("date"), dt.get("color"),
                             dt.get("created_at"), dt.get("note", "")))
                if "blocked_dates" in data:
                    for d in data["blocked_dates"]:
                        conn.execute("INSERT OR IGNORE INTO blocked_dates (date) VALUES (?)", (d,))
                if "achievements" in data:
                    for ach_id in data["achievements"]:
                        if isinstance(ach_id, str):
                            conn.execute(
                                "INSERT OR IGNORE INTO achievements (achievement_id, date_earned) VALUES (?, ?)",
                                (ach_id, today_str))
                conn.commit()

            new_name = OLD_JSON_PATH.parent / "storage.json"
            OLD_JSON_PATH.rename(new_name)
            print(f"[Storage] Migracja zakończona sukcesem. Stary plik: {new_name}")

        except Exception as e:
            print(f"[Storage] Błąd migracji JSON: {e}")

    def _migrate_to_relational_schema(self):
        with self._get_conn() as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(exams)")]

            if "subject_id" not in columns:
                try:
                    conn.execute("ALTER TABLE exams ADD COLUMN subject_id TEXT REFERENCES subjects(id) ON DELETE SET NULL")
                except sqlite3.OperationalError:
                    pass

            exams_to_fix = conn.execute("SELECT id, subject FROM exams WHERE subject_id IS NULL AND subject IS NOT NULL").fetchall()

            if not exams_to_fix:
                return

            default_sem_id = f"sem_{uuid.uuid4().hex[:8]}"
            existing_sem = conn.execute("SELECT id FROM semesters LIMIT 1").fetchone()

            if existing_sem:
                current_sem_id = existing_sem[0]
            else:
                conn.execute("""
                             INSERT INTO semesters (id, name, start_date, end_date, is_current)
                             VALUES (?, ?, ?, ?, ?)
                             """, (default_sem_id, "Domyślny (Migracja)", str(datetime.date.today()),
                                   str(datetime.date.today().replace(year=datetime.date.today().year + 1)), 1))
                current_sem_id = default_sem_id

            unique_subjects = set(e["subject"] for e in exams_to_fix)
            subject_map = {}

            for name in unique_subjects:
                existing_subj = conn.execute("SELECT id FROM subjects WHERE name=?", (name,)).fetchone()
                if existing_subj:
                    subject_map[name] = existing_subj[0]
                else:
                    new_sub_id = f"sub_{uuid.uuid4().hex[:8]}"
                    short = "".join([word[0].upper() for word in name.split() if word])[:3]
                    conn.execute("""
                                 INSERT INTO subjects (id, semester_id, name, short_name, color, weight)
                                 VALUES (?, ?, ?, ?, ?, ?)
                                 """, (new_sub_id, current_sem_id, name, short, None, 1.0))
                    subject_map[name] = new_sub_id

            for exam in exams_to_fix:
                s_name = exam["subject"]
                if s_name in subject_map:
                    new_sid = subject_map[s_name]
                    conn.execute("UPDATE exams SET subject_id=? WHERE id=?", (new_sid, exam["id"]))

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
        """Dodaje kolumnę 'time' do tabeli exams, jeśli nie istnieje."""
        with self._get_conn() as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(exams)")]
            if "time" not in columns:
                try:
                    conn.execute("ALTER TABLE exams ADD COLUMN time TEXT")
                except sqlite3.OperationalError:
                    pass
            conn.commit()

    # --- API (SETTINGS & STATS) ---

    def get_settings(self):
        res = {}
        with self._get_conn() as conn:
            rows = conn.execute("SELECT key, value FROM settings")
            for r in rows:
                try:
                    res[r["key"]] = json.loads(r["value"])
                except (json.JSONDecodeError, TypeError):
                    res[r["key"]] = r["value"]
        defaults = DEFAULT_DATA["settings"].copy()
        # Łączenie głębokie dla settings (ważne dla grading_system)
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
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO global_stats (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    def get_other_stats(self):
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
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO stats (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            conn.commit()

    # --- CUSTOM SOUNDS API (RETRO AUDIO LAB) ---

    def get_custom_sounds(self):
        """Zwraca listę słowników: {'id', 'name', 'steps'}"""
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM custom_sounds").fetchall()
            results = []
            for r in rows:
                d = dict(r)
                try:
                    d["steps"] = json.loads(d["steps_json"])
                except (json.JSONDecodeError, TypeError):
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
                except (json.JSONDecodeError, TypeError):
                    d["steps"] = []
                return d
            return None

    def add_custom_sound(self, sound_dict):
        """sound_dict: {'id', 'name', 'steps'}"""
        steps_json = json.dumps(sound_dict["steps"])
        with self._get_conn() as conn:
            conn.execute("INSERT OR REPLACE INTO custom_sounds (id, name, steps_json) VALUES (?, ?, ?)",
                         (sound_dict["id"], sound_dict["name"], steps_json))
            conn.commit()

    def delete_custom_sound(self, sound_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM custom_sounds WHERE id=?", (sound_id,))
            conn.commit()

    # --- API (EXAMS) ---

    def get_exam(self, exam_id):
        sql = """
              SELECT e.*, s.name as subject_name, s.color as subject_color
              FROM exams e
                       LEFT JOIN subjects s ON e.subject_id = s.id
              WHERE e.id = ? \
              """
        with self._get_conn() as conn:
            row = conn.execute(sql, (exam_id,)).fetchone()
            if row:
                data = dict(row)
                data["ignore_barrier"] = bool(data["ignore_barrier"])
                if data.get("subject_name"):
                    data["subject"] = data["subject_name"]
                return data
            return None

    def get_exams(self):
        sql = """
              SELECT e.*, s.name as subject_name, s.color as subject_color
              FROM exams e
                       LEFT JOIN subjects s ON e.subject_id = s.id \
              """
        with self._get_conn() as conn:
            rows = conn.execute(sql).fetchall()
            results = []
            for r in rows:
                d = dict(r)
                if d.get("subject_name"):
                    d["subject"] = d["subject_name"]
                if d.get("subject_color"):
                    d["color"] = d["subject_color"]
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
                         """, (
                             exam_dict["id"], subj_id, exam_dict["subject"], exam_dict["title"], exam_dict["date"],
                             exam_dict.get("time"),  # Dodana godzina
                             exam_dict.get("note", ""), 1 if exam_dict.get("ignore_barrier") else 0,
                             exam_dict.get("color")))
            conn.commit()

    def update_exam(self, exam_dict):
        with self._get_conn() as conn:
            conn.execute("""
                         UPDATE exams
                         SET subject=?, title=?, date=?, time=?, note=?, ignore_barrier=?, color=?
                         WHERE id = ?
                         """, (
                             exam_dict["subject"], exam_dict["title"], exam_dict["date"],
                             exam_dict.get("time"),  # Dodana godzina
                             exam_dict.get("note", ""), 1 if exam_dict.get("ignore_barrier") else 0,
                             exam_dict.get("color"),
                             exam_dict["id"]))
            conn.commit()

    def delete_exam(self, exam_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM exams WHERE id=?", (exam_id,))
            conn.commit()

    # --- API (TOPICS) ---

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
            if exam_id:
                return conn.execute("SELECT * FROM topics WHERE exam_id=?", (exam_id,)).fetchall()
            else:
                return conn.execute("SELECT * FROM topics").fetchall()

    def add_topic(self, topic_dict):
        with self._get_conn() as conn:
            conn.execute("""
                         INSERT INTO topics (id, exam_id, name, status, scheduled_date, locked, note)
                         VALUES (?, ?, ?, ?, ?, ?, ?)
                         """, (
                             topic_dict["id"], topic_dict["exam_id"], topic_dict["name"], topic_dict["status"],
                             topic_dict.get("scheduled_date"), 1 if topic_dict.get("locked") else 0,
                             topic_dict.get("note", "")))
            conn.commit()

    def update_topic(self, topic_dict):
        with self._get_conn() as conn:
            conn.execute("""
                         UPDATE topics
                         SET exam_id=?, name=?, status=?, scheduled_date=?, locked=?, note=?
                         WHERE id = ?
                         """, (
                             topic_dict["exam_id"], topic_dict["name"], topic_dict["status"],
                             topic_dict.get("scheduled_date"), 1 if topic_dict.get("locked") else 0,
                             topic_dict.get("note", ""),
                             topic_dict["id"]))
            conn.commit()

    def delete_topic(self, topic_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM topics WHERE id=?", (topic_id,))
            conn.commit()

    # --- API (DAILY TASKS) ---

    def get_daily_task(self, task_id):
        with self._get_conn() as conn:
            row = conn.execute("SELECT * FROM daily_tasks WHERE id=?", (task_id,)).fetchone()
            return dict(row) if row else None

    def get_daily_tasks(self):
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM daily_tasks").fetchall()

    def add_daily_task(self, task_dict):
        with self._get_conn() as conn:
            conn.execute("""
                         INSERT INTO daily_tasks (id, content, status, date, color, created_at, note)
                         VALUES (?, ?, ?, ?, ?, ?, ?)
                         """, (
                             task_dict["id"], task_dict["content"], task_dict["status"],
                             task_dict["date"], task_dict.get("color"), task_dict.get("created_at"),
                             task_dict.get("note", "")))
            conn.commit()

    def update_daily_task(self, task_dict):
        with self._get_conn() as conn:
            conn.execute("""
                         UPDATE daily_tasks
                         SET content=?,
                             status=?,
                             date=?,
                             color=?,
                             created_at=?,
                             note=?
                         WHERE id = ?
                         """, (
                             task_dict["content"], task_dict["status"], task_dict["date"],
                             task_dict.get("color"), task_dict.get("created_at"), task_dict.get("note", ""),
                             task_dict["id"]))
            conn.commit()

    def delete_daily_task(self, task_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM daily_tasks WHERE id=?", (task_id,))
            conn.commit()

    # --- API (OTHERS) ---

    def get_blocked_dates(self):
        with self._get_conn() as conn:
            return [row["date"] for row in conn.execute("SELECT date FROM blocked_dates")]

    def add_blocked_date(self, date_str):
        with self._get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO blocked_dates (date) VALUES (?)", (date_str,))
            conn.commit()

    def remove_blocked_date(self, date_str):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM blocked_dates WHERE date=?", (date_str,))
            conn.commit()

    def get_achievements(self):
        with self._get_conn() as conn:
            return [row["achievement_id"] for row in conn.execute("SELECT achievement_id FROM achievements")]

    def add_achievement(self, achievement_id):
        today = datetime.date.today().isoformat()
        with self._get_conn() as conn:
            conn.execute("INSERT OR IGNORE INTO achievements (achievement_id, date_earned) VALUES (?, ?)",
                         (achievement_id, today))
            conn.commit()

    # --- NOWE API (CRUD) ---

    def get_semesters(self):
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM semesters").fetchall()

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
            if semester_id:
                return conn.execute("SELECT * FROM subjects WHERE semester_id=?", (semester_id,)).fetchall()
            return conn.execute("SELECT * FROM subjects").fetchall()

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

    # --- SCHEDULE ENTRIES ---

    def get_schedule(self):
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM schedule_entries").fetchall()

    def get_schedule_entries_by_subject(self, subject_id):
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM schedule_entries WHERE subject_id=?", (subject_id,)).fetchall()

    def add_schedule_entry(self, entry_dict):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO schedule_entries (id, subject_id, day_of_week, start_time, end_time, room, type, period_start, period_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entry_dict["id"], entry_dict["subject_id"], entry_dict["day_of_week"], entry_dict["start_time"],
                 entry_dict["end_time"], entry_dict.get("room"), entry_dict.get("type"),
                 entry_dict.get("period_start"), entry_dict.get("period_end")))
            conn.commit()

    def delete_schedule_entry(self, entry_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM schedule_entries WHERE id=?", (entry_id,))
            conn.commit()

    # NOWE METODY DLA WYJĄTKÓW (ODWOŁANYCH ZAJĘĆ)
    def add_schedule_cancellation(self, entry_id, date_str):
        new_id = f"cancel_{uuid.uuid4().hex[:8]}"
        with self._get_conn() as conn:
            conn.execute("INSERT INTO schedule_cancellations (id, entry_id, date) VALUES (?, ?, ?)",
                         (new_id, entry_id, date_str))
            conn.commit()

    def get_schedule_cancellations(self):
        """Zwraca listę słowników: {'entry_id': '...', 'date': '...'}"""
        with self._get_conn() as conn:
            return conn.execute("SELECT entry_id, date FROM schedule_cancellations").fetchall()

    # --- GRADES ---

    def get_grades(self, subject_id=None):
        with self._get_conn() as conn:
            if subject_id:
                return conn.execute("SELECT * FROM grades WHERE subject_id=?", (subject_id,)).fetchall()
            return conn.execute("SELECT * FROM grades").fetchall()

    def add_grade(self, grade_dict):
        with self._get_conn() as conn:
            # Dodano module_id
            conn.execute("INSERT INTO grades (id, subject_id, module_id, value, weight, desc, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         (grade_dict["id"], grade_dict["subject_id"], grade_dict.get("module_id"),
                          grade_dict["value"], grade_dict.get("weight", 1.0),
                          grade_dict.get("desc"), grade_dict.get("date")))
            conn.commit()

    def delete_grade(self, grade_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM grades WHERE id=?", (grade_id,))
            conn.commit()

    def get_grade_modules(self, subject_id):
        with self._get_conn() as conn:
            return conn.execute("SELECT * FROM grade_modules WHERE subject_id=?", (subject_id,)).fetchall()

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

    # --- NOWE METODY DLA HISTORII ZADAŃ ---

    def get_task_history(self):
        """Zwraca zadania zakończone LUB zaległe (data < dzisiaj)."""
        today = str(datetime.date.today())
        with self._get_conn() as conn:
            # Pobieramy wszystko co jest 'done' LUB data jest w przeszłości i 'todo'
            # Sortujemy od najnowszych
            sql = """
                  SELECT * \
                  FROM daily_tasks
                  WHERE status = 'done' \
                     OR (date < ? AND status = 'todo')
                  ORDER BY date DESC \
                  """
            return conn.execute(sql, (today,)).fetchall()

    def clear_task_history(self, today_str):
        """Usuwa zadania z historii (done lub stare)."""
        with self._get_conn() as conn:
            sql = "DELETE FROM daily_tasks WHERE status = 'done' OR date < ?"
            conn.execute(sql, (today_str,))
            conn.commit()

    def restore_overdue_tasks(self, today_str):
        """Przenosi wszystkie niezrobione zadania z przeszłości na dzisiaj."""
        with self._get_conn() as conn:
            # 1. Policz ile takich jest
            count_sql = "SELECT count(*) FROM daily_tasks WHERE date < ? AND status = 'todo'"
            count = conn.execute(count_sql, (today_str,)).fetchone()[0]

            if count > 0:
                # 2. Zaktualizuj datę na dzisiaj
                update_sql = "UPDATE daily_tasks SET date = ? WHERE date < ? AND status = 'todo'"
                conn.execute(update_sql, (today_str, today_str))
                conn.commit()

            return count


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