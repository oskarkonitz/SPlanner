import customtkinter as ctk
from core.achievements_manager import AchievementManager
from gui.components.achievements_widgets import StaticAchievementItem, AccordionItem


class AchievementsPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, storage, btn_style, close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.storage = storage
        self.close_callback = close_callback

        # Inicjalizacja Managera ze storage
        self.manager = AchievementManager(self, txt, storage)

        # NAGŁÓWEK
        header_text = self.txt.get("ach_win_header_label", "🏆 Your Achievements")
        ctk.CTkLabel(self, text=header_text, font=("Arial", 20, "bold")).pack(pady=15)

        # SCROLLABLE FRAME
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=400)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.build_list()

        # PRZYCISK ZAMKNIJ
        ctk.CTkButton(self, text=self.txt.get("btn_close", "Close"), command=self.perform_close,
                      fg_color="transparent", border_width=1, border_color="gray", text_color=("gray10", "gray90")
                      ).pack(pady=10)

    def perform_close(self):
        if self.close_callback:
            self.close_callback()
        else:
            if hasattr(self, 'winfo_toplevel'):
                try:
                    self.winfo_toplevel().destroy()
                except:
                    pass

    def build_list(self):
        unlocked_ids = self.storage.get_achievements() if self.storage else []
        families = {}

        # --- MAPOWANIE GRUPOWE ---
        # Przypisujemy ID osiągnięcia do -> (Nazwa Grupy, Index kolejności w grupie)
        group_map = {
            # Grupa: Oceny (Grade Collector)
            "grade_bad_day": ("grade_collector", 0),
            "grade_close_call": ("grade_collector", 1),
            "grade_steady": ("grade_collector", 2),
            "grade_good_job": ("grade_collector", 3),
            "grade_high_flyer": ("grade_collector", 4),
            "grade_ace": ("grade_collector", 5),

            # Grupa: Średnia (GPA Milestones)
            "gpa_scholar": ("gpa_milestones", 0),
            "gpa_mastermind": ("gpa_milestones", 1)
        }

        # Kolejność wyświetlania rodzin
        order = [
            "first_step",
            "gradebook_first",
            "clean_sheet",
            "record_breaker",
            "busy_day",
            "hours_daily",
            "hours_total",
            "balance",
            "scribe",
            "encyclopedia",
            "time_lord",
            "session_master",
            "polyglot",
            "strategist",
            "grade_collector",  # Zgrupowane oceny
            "gpa_milestones",  # Zgrupowane średnie
            "limit_breaker",
            "comeback_king"
        ]

        family_meta = {}

        for ach_id, icon, title_key, desc_key, check_func, threshold in self.manager.definitions:

            # 1. Sprawdź czy to grupa manualna
            if ach_id in group_map:
                base, lvl = group_map[ach_id]
            else:
                # 2. Standardowa logika (suffix _1, _2...)
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
                # Pokazujemy postęp (x/y) tylko dla liczbowych intów, nie dla floatów (ocen)
                if isinstance(threshold, int):
                    current_val = self.manager.get_current_metric(check_func)
                    d_text += f" ({current_val}/{threshold})"

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
                "corner_text": corner_txt
            })

            # Domyślne metadane (pierwsze napotkane) - zostaną nadpisane dla grup manualnych
            if base not in family_meta and base not in group_map.values():
                clean_title = t_text.split(" I")[0].split(" IV")[0].strip()
                family_meta[base] = {"icon": icon, "title": clean_title}

        # --- NADPISANIE NAGŁÓWKÓW DLA NOWYCH GRUP ---
        # Tutaj definiujemy ikonę i tytuł całej zwijanej sekcji

        grade_title = self.txt.get("ach_grp_grades", "Grade Collector")
        family_meta["grade_collector"] = {"icon": "📊", "title": grade_title}

        gpa_title = self.txt.get("ach_grp_gpa", "GPA Milestones")
        family_meta["gpa_milestones"] = {"icon": "🎓", "title": gpa_title}

        # --- RENDEROWANIE ---
        for base in order:
            if base not in families: continue
            items = sorted(families[base], key=lambda x: x["lvl"])

            # Pobierz meta, jeśli brak (np. comeback_king) użyj pierwszego elementu
            if base in family_meta:
                meta = family_meta[base]
            else:
                meta = {"icon": "🏆", "title": items[0]["title"]}

            # Jeśli tylko 1 element i poziom 0 -> Statyczny
            if len(items) == 1 and items[0]["lvl"] == 0:
                item = items[0]
                StaticAchievementItem(
                    self.scroll_frame,
                    icon=items[0].get("icon", meta["icon"]) if base not in family_meta else meta["icon"],
                    # Fallback icon logic
                    title=item["title"],
                    desc=item["desc"],
                    is_unlocked=item["unlocked"],
                    corner_text=item.get("corner_text")
                ).pack(fill="x", pady=5)
            else:
                # Akordeon
                highest_lvl_idx = -1
                for i, it in enumerate(items):
                    if it["unlocked"]: highest_lvl_idx = i

                is_unlocked_any = highest_lvl_idx >= 0

                # Tytuł nagłówka: Jeśli odblokowano coś, pokazujemy to, jeśli nie - ogólny tytuł grupy
                if is_unlocked_any and base not in ["grade_collector", "gpa_milestones"]:
                    # Dla standardowych (Level I, II) pokazujemy aktualny poziom w nagłówku
                    display_title = items[highest_lvl_idx]["title"]
                else:
                    # Dla grup (Oceny) zawsze pokazujemy nazwę grupy w nagłówku
                    display_title = meta["title"]

                level_suffix = ""
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
                    corner_text=display_corner
                ).pack(fill="x", pady=5)