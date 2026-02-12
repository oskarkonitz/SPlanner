import customtkinter as ctk
from core.achievements_manager import AchievementManager
from gui.components.achievements_widgets import StaticAchievementItem, AccordionItem

class AchievementsWindow:
    def __init__(self, parent, txt, storage, btn_style):
        self.txt = txt
        self.storage = storage
        # Inicjalizacja Managera ze storage
        self.manager = AchievementManager(parent, txt, storage)
        self.win = ctk.CTkToplevel(parent)
        self.win.title(self.txt.get("win_achievements", "Achievements"))
        self.win.geometry("500x650")
        self.win.resizable(False, True)

        header_text = self.txt.get("ach_win_header_label", "🏆 Your Achievements")
        ctk.CTkLabel(self.win, text=header_text, font=("Arial", 20, "bold")).pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self.win, width=460, height=500)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.build_list()

        ctk.CTkButton(self.win, text=self.txt["btn_close"], command=self.win.destroy,
                      fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90")
                      ).pack(pady=10)

    def build_list(self):
        # Pobieramy ID odblokowanych z bazy SQL
        unlocked_ids = self.storage.get_achievements() if self.storage else []

        families = {}
        order = ["first_step", "clean_sheet", "record_breaker", "hours_daily", "hours_total",
                 "balance", "scribe", "encyclopedia", "time_lord", "session_master", "polyglot", "strategist"]
        family_meta = {}

        for ach_id, icon, title_key, desc_key, check_func, threshold in self.manager.definitions:
            parts = ach_id.rsplit('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                base = parts[0]
                lvl = int(parts[1])
            else:
                base = ach_id
                lvl = 0

            if base not in families: families[base] = []

            t_text = self.txt.get(title_key, title_key)
            d_text = self.txt.get(desc_key, desc_key)

            is_unlocked = ach_id in unlocked_ids

            if not is_unlocked and threshold is not None:
                current_val = self.manager.get_current_metric(check_func)
                d_text += f" ({current_val}/{threshold})"

            # --- MODYFIKACJA: Wyświetlanie rekordu dla Rocket w rogu (HH:MM) ---
            corner_txt = None
            if ach_id == "record_breaker" and self.storage:
                stats = self.storage.get_global_stats()
                best_sec = int(stats.get("all_time_best_time", 0))
                h = best_sec // 3600
                m = (best_sec % 3600) // 60
                corner_txt = f"{h:02d}:{m:02d}"

            families[base].append({
                "id": ach_id, "lvl": lvl, "title": t_text, "desc": d_text,
                "unlocked": is_unlocked,
                "corner_text": corner_txt  # Przekazujemy tekst do rogu
            })
            if base not in family_meta:
                clean_title = t_text.split(" I")[0].split(" IV")[0].strip()
                family_meta[base] = {"icon": icon, "title": clean_title}

        for base in order:
            if base not in families: continue
            items = sorted(families[base], key=lambda x: x["lvl"])
            meta = family_meta[base]

            if len(items) == 1 and items[0]["lvl"] == 0:
                item = items[0]
                StaticAchievementItem(
                    self.scroll_frame,
                    icon=meta["icon"],
                    title=item["title"],
                    desc=item["desc"],
                    is_unlocked=item["unlocked"],
                    corner_text=item.get("corner_text")  # Przekazujemy
                ).pack(fill="x", pady=5)
            else:
                highest_lvl_idx = -1
                for i, it in enumerate(items):
                    if it["unlocked"]: highest_lvl_idx = i

                is_unlocked_any = highest_lvl_idx >= 0

                display_title = items[highest_lvl_idx]["title"] if is_unlocked_any else meta["title"]
                level_suffix = ""

                # Jeśli którykolwiek element ma corner_text, bierzemy go
                display_corner = next((it.get("corner_text") for it in items if it.get("corner_text")), None)

                details = []
                for it in items:
                    details.append((it["title"], it["desc"], it["unlocked"]))

                AccordionItem(
                    self.scroll_frame,
                    self.txt,
                    icon=meta["icon"],
                    title=display_title,
                    level_text=level_suffix,
                    details_list=details,
                    is_unlocked=is_unlocked_any,
                    corner_text=display_corner  # Przekazujemy
                ).pack(fill="x", pady=5)