from core.sound import play_event_sound
from core.planner import date_format
from datetime import date

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
        ]

    def check_all(self, silent=False):
        if not self.storage:
            return

        # Pobieramy listę odblokowanych osiągnięć z bazy SQL
        unlocked_ids = self.storage.get_achievements()
        new_unlocks = []

        for ach_id, icon, title_key, desc_key, check_func, threshold in self.definitions:
            if ach_id in unlocked_ids:
                continue

            is_unlocked = check_func(threshold) if threshold is not None else check_func()

            if is_unlocked:
                # Zapisujemy nowe osiągnięcie w bazie SQL
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

        # --- ODTWARZANIE DŹWIĘKU ---
        if self.storage:
            play_event_sound(self.storage, "sound_achievement")
        # ---------------------------

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

    def get_current_metric(self, check_func):
        if not self.storage:
            return 0

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
            sec = stats.get("daily_study_time", 0)
            return round(sec / 3600, 1)
        elif check_func == self._check_total_hours:
            sec = stats.get("total_study_time", 0)
            return int(sec / 3600)
        elif check_func == self._check_new_record:
            return 1 if self._check_new_record() else 0
        else:
            return 0

    def _check_first_step(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("topics_done", 0) >= threshold

    def _check_clean_sheet(self):
        today = date.today()
        # Pobieramy dane z SQL
        exams = self.storage.get_exams()
        topics = self.storage.get_topics()
        stats = self.storage.get_global_stats()

        active_exams_ids = {e["id"] for e in exams if date_format(e["date"]) >= today}
        overdue_count = 0

        for t in topics:
            if t.get("scheduled_date") and date_format(t["scheduled_date"]) < today:
                if t["status"] == "todo" and t["exam_id"] in active_exams_ids:
                    overdue_count += 1

        had_overdue = stats.get("had_overdue", False)
        if overdue_count > 0:
            if not had_overdue:
                # Aktualizujemy flagę w SQL
                self.storage.update_global_stat("had_overdue", True)
            return False
        else:
            return had_overdue

    def _check_balance(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("days_off", 0) >= threshold

    def _check_scribe(self, threshold):
        stats = self.storage.get_global_stats()
        return stats.get("notes_added", 0) >= threshold

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
        exams = self.storage.get_exams()
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

        if best == 0:
            return False

        return current > best and current > 60