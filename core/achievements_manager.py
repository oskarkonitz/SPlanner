from core.sound import play_event_sound
from core.planner import date_format
from datetime import date
from gui.dialogs.achievements_popup import UnlockPopup


class AchievementManager:
    def __init__(self, parent_window, txt, storage=None):
        self.parent = parent_window
        self.txt = txt
        self.storage = storage
        self.notification_queue = []
        self.deferred_queue = []
        self.is_showing_popup = False

        self.definitions = [
            ("first_step", "👶", "ach_first_step", "ach_desc_first_step", self._check_first_step, 1),
            ("clean_sheet", "🧹", "ach_clean_sheet", "ach_desc_clean_sheet", self._check_clean_sheet, None),

            # --- POZIOMY DLA MARATHON RUNNER (Daily Hours) ---
            ("hours_daily_1", "⏳", "ach_hours_daily_1", "ach_desc_hours_daily_1", self._check_daily_hours, 1),
            ("hours_daily_2", "⏳", "ach_hours_daily_2", "ach_desc_hours_daily_2", self._check_daily_hours, 2),
            ("hours_daily_3", "⏳", "ach_hours_daily_3", "ach_desc_hours_daily_3", self._check_daily_hours, 4),
            ("hours_daily_4", "⏳", "ach_hours_daily_4", "ach_desc_hours_daily_4", self._check_daily_hours, 6),

            # --- POZIOMY DLA DEDICATED (Total Hours) ---
            ("hours_total_1", "⌛", "ach_hours_total_1", "ach_desc_hours_total_1", self._check_total_hours, 10),
            ("hours_total_2", "⌛", "ach_hours_total_2", "ach_desc_hours_total_2", self._check_total_hours, 50),
            ("hours_total_3", "⌛", "ach_hours_total_3", "ach_desc_hours_total_3", self._check_total_hours, 100),
            ("hours_total_4", "⌛", "ach_hours_total_4", "ach_desc_hours_total_4", self._check_total_hours, 200),

            # --- REKORD ---
            ("record_breaker", "🚀", "ach_record_breaker", "ach_desc_record_breaker", self._check_new_record, None),

            ("balance", "🏖️", "ach_balance", "ach_desc_balance", self._check_balance, 1),
            ("balance_2", "🏖️", "ach_balance_2", "ach_desc_balance_2", self._check_balance, 3),
            ("balance_3", "🏖️", "ach_balance_3", "ach_desc_balance_3", self._check_balance, 7),
            ("balance_4", "🏖️", "ach_balance_4", "ach_desc_balance_4", self._check_balance, 14),
            ("balance_5", "🏖️", "ach_balance_5", "ach_desc_balance_5", self._check_balance, 20),
            ("balance_6", "🏖️", "ach_balance_6", "ach_desc_balance_6", self._check_balance, 60),
            ("balance_7", "🏖️", "ach_balance_7", "ach_desc_balance_7", self._check_balance, 360),
            ("scribe_1", "✍", "ach_scribe_1", "ach_desc_scribe_1", self._check_scribe, 5),
            ("scribe_2", "✍", "ach_scribe_2", "ach_desc_scribe_2", self._check_scribe, 10),
            ("scribe_3", "✍", "ach_scribe_3", "ach_desc_scribe_3", self._check_scribe, 25),
            ("scribe_4", "✍", "ach_scribe_4", "ach_desc_scribe_4", self._check_scribe, 50),
            ("scribe_5", "✍", "ach_scribe_5", "ach_desc_scribe_5", self._check_scribe, 100),
            ("scribe_6", "✍", "ach_scribe_6", "ach_desc_scribe_6", self._check_scribe, 250),
            ("scribe_7", "✍", "ach_scribe_7", "ach_desc_scribe_7", self._check_scribe, 500),
            ("scribe_8", "✍", "ach_scribe_8", "ach_desc_scribe_8", self._check_scribe, 1000),
            ("scribe_9", "✍", "ach_scribe_9", "ach_desc_scribe_9", self._check_scribe, 2000),
            ("encyclopedia_1", "📚", "ach_encyclopedia_1", "ach_desc_encyclopedia_1", self._check_encyclopedia, 10),
            ("encyclopedia_2", "📚", "ach_encyclopedia_2", "ach_desc_encyclopedia_2", self._check_encyclopedia, 25),
            ("encyclopedia_3", "📚", "ach_encyclopedia_3", "ach_desc_encyclopedia_3", self._check_encyclopedia, 50),
            ("encyclopedia_4", "📚", "ach_encyclopedia_4", "ach_desc_encyclopedia_4", self._check_encyclopedia, 100),
            ("encyclopedia_5", "📚", "ach_encyclopedia_5", "ach_desc_encyclopedia_5", self._check_encyclopedia, 200),
            ("encyclopedia_6", "📚", "ach_encyclopedia_6", "ach_desc_encyclopedia_6", self._check_encyclopedia, 250),
            ("encyclopedia_7", "📚", "ach_encyclopedia_7", "ach_desc_encyclopedia_7", self._check_encyclopedia, 500),
            ("encyclopedia_8", "📚", "ach_encyclopedia_8", "ach_desc_encyclopedia_8", self._check_encyclopedia, 1000),
            ("encyclopedia_9", "📚", "ach_encyclopedia_9", "ach_desc_encyclopedia_9", self._check_encyclopedia, 2000),
            ("time_lord_1", "🍅", "ach_time_lord_1", "ach_desc_time_lord_1", self._check_time_lord, 5),
            ("time_lord_2", "🍅", "ach_time_lord_2", "ach_desc_time_lord_2", self._check_time_lord, 10),
            ("time_lord_3", "🍅", "ach_time_lord_3", "ach_desc_time_lord_3", self._check_time_lord, 25),
            ("time_lord_4", "🍅", "ach_time_lord_4", "ach_desc_time_lord_4", self._check_time_lord, 50),
            ("time_lord_5", "🍅", "ach_time_lord_5", "ach_desc_time_lord_5", self._check_time_lord, 100),
            ("time_lord_6", "🍅", "ach_time_lord_6", "ach_desc_time_lord_6", self._check_time_lord, 500),
            ("time_lord_7", "🍅", "ach_time_lord_7", "ach_desc_time_lord_7", self._check_time_lord, 1000),
            ("session_master_1", "🎓", "ach_session_master_1", "ach_desc_session_master_1", self._check_session_master,
             1),
            ("session_master_2", "🎓", "ach_session_master_2", "ach_desc_session_master_2", self._check_session_master,
             3),
            ("session_master_3", "🎓", "ach_session_master_3", "ach_desc_session_master_3", self._check_session_master,
             5),
            ("session_master_4", "🎓", "ach_session_master_4", "ach_desc_session_master_4", self._check_session_master,
             10),
            ("session_master_5", "🎓", "ach_session_master_5", "ach_desc_session_master_5", self._check_session_master,
             20),
            ("session_master_6", "🎓", "ach_session_master_6", "ach_desc_session_master_6", self._check_session_master,
             100),
            ("session_master_7", "🎓", "ach_session_master_7", "ach_desc_session_master_7", self._check_session_master,
             250),
            ("polyglot_1", "🌍", "ach_polyglot_1", "ach_desc_polyglot_1", self._check_polyglot, 2),
            ("polyglot_2", "🌍", "ach_polyglot_2", "ach_desc_polyglot_2", self._check_polyglot, 3),
            ("polyglot_3", "🌍", "ach_polyglot_3", "ach_desc_polyglot_3", self._check_polyglot, 5),
            ("polyglot_4", "🌍", "ach_polyglot_4", "ach_desc_polyglot_4", self._check_polyglot, 10),
            ("polyglot_5", "🌍", "ach_polyglot_5", "ach_desc_polyglot_5", self._check_polyglot, 20),
            ("polyglot_6", "🌍", "ach_polyglot_6", "ach_desc_polyglot_6", self._check_polyglot, 50),
            ("polyglot_7", "🌍", "ach_polyglot_7", "ach_desc_polyglot_7", self._check_polyglot, 100),
            ("polyglot_8", "🌍", "ach_polyglot_8", "ach_desc_polyglot_8", self._check_polyglot, 500),
            ("strategist_1", "📅", "ach_strategist_1", "ach_desc_strategist_1", self._check_strategist, 7),
            ("strategist_2", "📅", "ach_strategist_2", "ach_desc_strategist_2", self._check_strategist, 14),
            ("strategist_3", "📅", "ach_strategist_3", "ach_desc_strategist_3", self._check_strategist, 30),
            ("strategist_4", "📅", "ach_strategist_4", "ach_desc_strategist_4", self._check_strategist, 60),

            # --- NOWE OSIĄGNIĘCIA OCEN (Grades) ---
            ("grade_bad_day", "🌧️", "ach_grade_bad_day", "ach_desc_grade_bad_day", self._check_grade_specific, 2.0),
            ("grade_close_call", "😅", "ach_grade_close_call", "ach_desc_grade_close_call", self._check_grade_specific,
             3.0),
            ("grade_steady", "🧱", "ach_grade_steady", "ach_desc_grade_steady", self._check_grade_specific, 3.5),
            ("grade_good_job", "👍", "ach_grade_good_job", "ach_desc_grade_good_job", self._check_grade_specific, 4.0),
            ("grade_high_flyer", "✈️", "ach_grade_high_flyer", "ach_desc_grade_high_flyer", self._check_grade_specific,
             4.5),
            ("grade_ace", "🌟", "ach_grade_ace", "ach_desc_grade_ace", self._check_grade_specific, 5.0),

            ("gpa_scholar", "🎓", "ach_gpa_scholar", "ach_desc_gpa_scholar", self._check_gpa, 4.0),
            ("gpa_mastermind", "🧠", "ach_gpa_mastermind", "ach_desc_gpa_mastermind", self._check_gpa, 4.75),

            ("limit_breaker", "🚀", "ach_limit_breaker", "ach_desc_limit_breaker", self._check_grade_limit_breaker,
             None),
            ("comeback_king", "👑", "ach_comeback_king", "ach_desc_comeback_king", self._check_comeback_king, None),
            ("gradebook_first", "📒", "ach_gradebook_first", "ach_desc_gradebook_first", self._check_gradebook, None),

            # --- BUSY DAY (Zadania jednego dnia) ---
            ("busy_day_1", "🔥", "ach_busy_day_1", "ach_desc_busy_day_1", self._check_busy_day, 10),
            ("busy_day_2", "🔥", "ach_busy_day_2", "ach_desc_busy_day_2", self._check_busy_day, 15),
            ("busy_day_3", "🔥", "ach_busy_day_3", "ach_desc_busy_day_3", self._check_busy_day, 20),
            ("busy_day_4", "🔥", "ach_busy_day_4", "ach_desc_busy_day_4", self._check_busy_day, 30),
        ]

    def check_all(self, silent=False):
        if not self.storage:
            return

        unlocked_ids = self.storage.get_achievements()
        new_unlocks = []

        for ach_id, icon, title_key, desc_key, check_func, threshold in self.definitions:
            if ach_id in unlocked_ids:
                continue

            is_unlocked = check_func(threshold) if threshold is not None else check_func()

            if is_unlocked:
                self.storage.add_achievement(ach_id)
                new_unlocks.append((icon, title_key, desc_key))

        if new_unlocks:
            if silent:
                self.deferred_queue.extend(new_unlocks)
            else:
                self.notification_queue.extend(new_unlocks)
                self.process_queue()

    def process_queue(self):
        if self.is_showing_popup or not self.notification_queue:
            return

        if self.storage:
            play_event_sound(self.storage, "sound_achievement")

        self.is_showing_popup = True
        icon, title_key, desc_key = self.notification_queue.pop(0)
        UnlockPopup(self.parent, self.txt, icon, title_key, desc_key, on_close=self.on_popup_closed)

    def flush_deferred(self):
        if self.deferred_queue:
            self.notification_queue.extend(self.deferred_queue)
            self.deferred_queue.clear()
            self.process_queue()

    def on_popup_closed(self):
        self.is_showing_popup = False
        self.parent.after(200, self.process_queue)

    # --- METRYKI (DLA POSTĘPU) ---
    def get_current_metric(self, check_func):
        if not self.storage: return 0
        stats = self.storage.get_global_stats()

        if check_func == self._check_first_step:
            return stats.get("topics_done", 0)
        elif check_func == self._check_balance:
            return stats.get("days_off", 0)
        elif check_func == self._check_scribe:
            return stats.get("notes_added", 0)
        elif check_func == self._check_encyclopedia:
            return stats.get("topics_done", 0)
        elif check_func == self._check_time_lord:
            return stats.get("pomodoro_sessions", 0)
        elif check_func == self._check_polyglot:
            return stats.get("exams_added", 0)
        elif check_func == self._check_session_master:
            return self._get_session_master_count()
        elif check_func == self._check_strategist:
            return self._get_max_strategy_days()
        elif check_func == self._check_daily_hours:
            return round(stats.get("daily_study_time", 0) / 3600, 1)
        elif check_func == self._check_total_hours:
            return int(stats.get("total_study_time", 0) / 3600)
        elif check_func == self._check_new_record:
            return 1 if self._check_new_record() else 0
        elif check_func == self._check_busy_day:
            return self._calculate_busy_day_score()
        else:
            return 0

    # --- LOGIKA NOWYCH OSIĄGNIĘĆ ---

    def _convert_to_grade_scale(self, val):
        if val <= 5.0: return val
        if val >= 90: return 5.0
        if val >= 80: return 4.5
        if val >= 70: return 4.0
        if val >= 60: return 3.5
        if val >= 50: return 3.0
        return 2.0

    def _check_grade_specific(self, target_grade):
        subjects = [dict(s) for s in self.storage.get_subjects()]

        for sub in subjects:
            grades = self.storage.get_grades(sub["id"])
            if not grades: continue

            # Obliczanie ostatecznej oceny z tego przedmiotu
            w_sum = sum(g["value"] * g["weight"] for g in grades)
            w_total = sum(g["weight"] for g in grades)
            if w_total == 0: continue

            avg = w_sum / w_total
            grade_val = self._convert_to_grade_scale(avg)

            # Jeśli ostateczna ocena z jakiegokolwiek przedmiotu pasuje, odblokowujemy
            if grade_val == target_grade:
                return True

        return False

    def _check_gpa(self, threshold):
        subjects = [dict(s) for s in self.storage.get_subjects()]
        if not subjects: return False

        total_ects = 0
        weighted_sum = 0

        for sub in subjects:
            grades = self.storage.get_grades(sub["id"])

            # BLOKADA: Sprawdzamy, czy ten przedmiot ma chociaż jedną ocenę
            if not grades:
                return False

            w_sum = sum(g["value"] * g["weight"] for g in grades)
            w_total = sum(g["weight"] for g in grades)
            if w_total == 0:
                return False

            avg = w_sum / w_total
            grade_val = self._convert_to_grade_scale(avg)

            ects = sub.get("weight", 1.0)
            weighted_sum += grade_val * ects
            total_ects += ects

        if total_ects == 0: return False
        gpa = weighted_sum / total_ects
        return gpa >= threshold

    def _check_grade_limit_breaker(self):
        grades = self.storage.get_grades()
        for g in grades:
            if g["value"] > 100: return True
        return False

    def _check_comeback_king(self):
        grades = self.storage.get_grades()
        subj_map = {}
        for g in grades:
            sid = g["subject_id"]
            if sid not in subj_map: subj_map[sid] = []
            subj_map[sid].append(self._convert_to_grade_scale(g["value"]))

        for sid, g_list in subj_map.items():
            if 2.0 in g_list and 5.0 in g_list:
                return True
        return False

    def _check_gradebook(self):
        grades = self.storage.get_grades()
        return len(grades) > 0

    def _calculate_busy_day_score(self):
        today_str = str(date.today())

        # FIX: Konwersja na słowniki dla bezpieczeństwa metod .get()
        daily_tasks = [dict(t) for t in self.storage.get_daily_tasks()]

        count_tasks = sum(1 for t in daily_tasks if t.get("date") == today_str and t["status"] == "done")

        # FIX: Konwersja na słowniki
        topics = [dict(t) for t in self.storage.get_topics()]
        count_topics = sum(1 for t in topics if str(t.get("scheduled_date")) == today_str and t["status"] == "done")

        return count_tasks + count_topics

    def _check_busy_day(self, threshold):
        return self._calculate_busy_day_score() >= threshold

    # --- STARE METODY (POPRAWIONE KONWERSJE) ---

    def _check_first_step(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("topics_done", 0) >= threshold

    def _check_clean_sheet(self):
        today = date.today()
        # FIX: Konwersja topics na dict, exams na dict
        exams = [dict(e) for e in self.storage.get_exams()]
        topics = [dict(t) for t in self.storage.get_topics()]
        stats = self.storage.get_global_stats()

        active_exams_ids = {e["id"] for e in exams if date_format(e["date"]) >= today}
        overdue_count = 0

        for t in topics:
            # Teraz bezpieczne .get()
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < today:
                if t["status"] == "todo" and t["exam_id"] in active_exams_ids:
                    overdue_count += 1

        had_overdue = stats.get("had_overdue", False)
        if overdue_count > 0:
            if not had_overdue:
                self.storage.update_global_stat("had_overdue", True)
            return False
        else:
            return had_overdue

    def _check_balance(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("days_off", 0) >= threshold

    def _check_scribe(self, threshold):
        stats = self.storage.get_global_stats()
        raw_val = stats.get("notes_added", 0)

        # Bezpieczna konwersja do porównania
        try:
            current_notes = int(raw_val)
        except (ValueError, TypeError):
            current_notes = 0

        return current_notes >= threshold

    def _check_encyclopedia(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("topics_done", 0) >= threshold

    def _check_time_lord(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("pomodoro_sessions", 0) >= threshold

    def _check_polyglot(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("exams_added", 0) >= threshold

    def _get_session_master_count(self):
        topics = self.storage.get_topics()
        exam_counts = {}
        for t in topics:
            eid = t["exam_id"]
            if eid not in exam_counts: exam_counts[eid] = [0, 0]
            exam_counts[eid][0] += 1
            if t["status"] == "done": exam_counts[eid][1] += 1
        completed = 0
        for eid, counts in exam_counts.items():
            if counts[0] >= 3 and counts[0] == counts[1]: completed += 1
        return completed

    def _check_session_master(self, threshold):
        return self._get_session_master_count() >= threshold

    def _get_max_strategy_days(self):
        today = date.today()
        exams = [dict(e) for e in self.storage.get_exams()]  # Dla pewności konwersja
        max_days = 0
        for e in exams:
            diff = (date_format(e["date"]) - today).days
            if diff > max_days: max_days = diff
        return max_days

    def _check_strategist(self, threshold):
        return self._get_max_strategy_days() >= threshold

    def _check_daily_hours(self, threshold_hours):
        stats = self.storage.get_global_stats()
        seconds = stats.get("daily_study_time", 0)
        return (seconds / 3600) >= threshold_hours

    def _check_total_hours(self, threshold_hours):
        stats = self.storage.get_global_stats()
        seconds = stats.get("total_study_time", 0)
        return (seconds / 3600) >= threshold_hours

    def _check_new_record(self, threshold=None):
        stats = self.storage.get_global_stats()
        current = stats.get("daily_study_time", 0)
        best = stats.get("all_time_best_time", 0)
        if best == 0: return False
        return current > best and current > 60