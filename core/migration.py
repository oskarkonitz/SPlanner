import json
from datetime import date
from core.storage import SQLiteProvider, SupabaseProvider


class DataMigrator:
    def __init__(self, local_provider: SQLiteProvider, supabase_url, supabase_key):
        self.local = local_provider
        self.cloud = SupabaseProvider(supabase_url, supabase_key)

    def run(self, progress_callback=None):
        def log(msg):
            if progress_callback: progress_callback(msg)
            print(f"[Migration] {msg}")

        try:
            log("Inicjalizacja migracji...")

            # 1. Ustawienia i Statystyki
            log("Migracja ustawień i statystyk...")
            settings = self.local.get_settings()
            for k, v in settings.items():
                self.cloud.update_setting(k, v)

            g_stats = self.local.get_global_stats()
            for k, v in g_stats.items():
                self.cloud.update_global_stat(k, v)

            # 2. Tabele proste (Dźwięki, Daty, Osiągnięcia)
            log("Migracja dźwięków i kalendarza...")
            for s in self.local.get_custom_sounds():
                self.cloud.add_custom_sound(s)
            for d in self.local.get_blocked_dates():
                self.cloud.add_blocked_date(d)
            for a in self.local.get_achievements():
                self.cloud.add_achievement(a)

            # 3. Struktura Akademicka (Kolejność: Semestry -> Przedmioty)
            log("Migracja struktury semestrów...")
            for sem in self.local.get_semesters():
                self.cloud.add_semester(dict(sem))

            for sub in self.local.get_subjects():
                self.cloud.add_subject(dict(sub))

            # 4. Grafik (Kolejność: Listy -> Wydarzenia)
            log("Migracja grafiku i kategorii...")
            for ev_list in self.local.get_event_lists():
                self.cloud.add_event_list(dict(ev_list))

            for ev in self.local.get_custom_events():
                self.cloud.add_custom_event(dict(ev))

            # 5. Edukacja (Egzaminy i Tematy)
            log("Migracja egzaminów...")
            for ex in self.local.get_exams():
                self.cloud.add_exam(dict(ex))

            topics = self.local.get_topics()
            if topics:
                # Mapowanie locked na boolean dla Supabase
                for t in topics:
                    t["locked"] = bool(t.get("locked", 0))
                self.cloud.update_topics_bulk(topics)

            # 6. Oceny i Moduły
            log("Migracja ocen...")
            # Pobieramy wszystkie przedmioty, aby przejść przez ich moduły i oceny
            subjects = self.local.get_subjects()
            for s in subjects:
                for mod in self.local.get_grade_modules(s["id"]):
                    self.cloud.add_grade_module(dict(mod))
                for grade in self.local.get_grades(s["id"]):
                    # SupabaseProvider obsłuży mapowanie desc -> desc_text
                    self.cloud.add_grade(dict(grade))

            # 7. Plan lekcji i Zadania
            log("Migracja planu i zadań...")
            for entry in self.local.get_schedule():
                self.cloud.add_schedule_entry(dict(entry))

            for cancel in self.local.get_schedule_cancellations():
                self.cloud.add_schedule_cancellation(cancel["entry_id"], cancel["date"])

            for t_list in self.local.get_task_lists():
                self.cloud.add_task_list(dict(t_list))

            for task in self.local.get_daily_tasks():
                self.cloud.add_daily_task(dict(task))

            log("Migracja zakończona sukcesem!")
            return True, "Success"

        except Exception as e:
            error_msg = str(e)
            log(f"Błąd: {error_msg}")
            return False, error_msg