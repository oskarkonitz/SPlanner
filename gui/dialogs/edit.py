import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
import uuid
import random
from datetime import datetime, timedelta
import re

def select_edit_item(parent, txt, tree, btn_style, callback=None, storage=None, drawer=None):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showinfo(txt["msg_info"], txt["msg_select_edit"])
        return

    item_id = selected_item[0]

    if not storage:
        messagebox.showerror(txt["msg_error"], "StorageManager is missing!")
        return

    target_exam = storage.get_exam(item_id)

    if target_exam:
        if drawer:
            drawer.set_content(EditExamPanel, txt=txt, btn_style=btn_style, exam_data=target_exam,
                               callback=callback, storage=storage, close_callback=drawer.close_panel)
        else:
            top = ctk.CTkToplevel(parent)
            top.title("Edit Exam")
            EditExamPanel(top, txt, btn_style, target_exam, callback, storage).pack(fill="both", expand=True)
        return

    target_topic = storage.get_topic(item_id)

    if target_topic:
        if drawer:
            drawer.set_content(EditTopicPanel, txt=txt, btn_style=btn_style, topic_data=target_topic,
                               callback=callback, storage=storage, close_callback=drawer.close_panel)
        else:
            top = ctk.CTkToplevel(parent)
            top.title("Edit Topic")
            EditTopicPanel(top, txt, btn_style, target_topic, callback, storage).pack(fill="both", expand=True)
        return

    messagebox.showerror(txt["msg_error"], txt["msg_cant_edit"])


# --- EDYCJA EGZAMINU ---
class EditExamPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, exam_data, callback=None, storage=None, close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.exam_data = exam_data
        self.callback = callback
        self.storage = storage
        self.close_callback = close_callback

        self.db_subjects = []
        self.subject_names = []
        self.semesters = []

        if self.storage:
            self.db_subjects = [dict(s) for s in self.storage.get_subjects()]
            self.subject_names = [s["name"] for s in self.db_subjects]
            self.semesters = [dict(s) for s in self.storage.get_semesters()]

        # CENTROWANIE
        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(expand=True, fill="x", padx=30)
        self.center_box.grid_columnconfigure(0, weight=1)
        self.center_box.grid_columnconfigure(1, weight=2)

        # NAGŁÓWEK
        header_title = self.txt["win_edit_exam_title"].format(subject=exam_data["subject"])
        ctk.CTkLabel(self.center_box, text=header_title, font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                          pady=(0, 20))

        # 1. PRZEDMIOT
        ctk.CTkLabel(self.center_box, text=self.txt["form_subject"]).grid(row=1, column=0, pady=5, padx=10, sticky="e")

        subj_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        subj_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        self.combo_subject = ctk.CTkComboBox(subj_frame, values=self.subject_names)
        self.combo_subject.pack(side="left", fill="x", expand=True)
        self.combo_subject.set(exam_data["subject"])

        self.btn_sem_filter = ctk.CTkButton(subj_frame, text="📅", width=35,
                                            fg_color="transparent", border_width=1, border_color="gray",
                                            text_color=("gray10", "gray90"),
                                            command=self.open_semester_menu)
        self.btn_sem_filter.pack(side="left", padx=(5, 0))

        # 2. TYTUŁ
        ctk.CTkLabel(self.center_box, text=self.txt["form_type"]).grid(row=2, column=0, pady=5, padx=10, sticky="e")
        self.ent_title = ctk.CTkEntry(self.center_box)
        self.ent_title.insert(0, exam_data["title"])
        self.ent_title.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # 3. DATA
        ctk.CTkLabel(self.center_box, text=self.txt["form_date"]).grid(row=3, column=0, pady=5, padx=10, sticky="e")

        date_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        date_frame.grid(row=3, column=1, padx=10, pady=5, sticky="w")
        self.ent_date = DateEntry(date_frame, width=15, date_pattern='y-mm-dd', background='#3a3a3a',
                                  foreground='white', borderwidth=0)
        self.ent_date.pack()

        if exam_data["date"]:
            self.ent_date.set_date(exam_data["date"])

        # 4. CZAS
        ctk.CTkLabel(self.center_box, text=self.txt.get("form_time", "Time (HH:MM)")).grid(row=4, column=0, pady=5,
                                                                                           padx=10, sticky="e")
        self.ent_time = ctk.CTkEntry(self.center_box)
        current_time = exam_data.get("time") or "09:00"
        self.ent_time.insert(0, current_time)
        self.ent_time.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # 5. BARIERA
        self.var_ignore_barrier = tk.BooleanVar(value=exam_data.get("ignore_barrier", False))
        cb_text = self.txt.get("form_ignore_barrier", "Ignoruj w planowaniu (Bariera)")
        self.cb_barrier = ctk.CTkCheckBox(self.center_box, text=cb_text, variable=self.var_ignore_barrier,
                                          onvalue=True, offvalue=False)
        self.cb_barrier.grid(row=5, column=0, columnspan=2, pady=(15, 5))

        # 6. TEMATY
        ctk.CTkLabel(self.center_box, text=self.txt["form_topics_edit"]).grid(row=7, column=0, pady=(10, 5),
                                                                              columnspan=2)
        self.txt_topics = ctk.CTkTextbox(self.center_box, height=120)
        self.txt_topics.grid(row=8, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="ew")

        # Ładowanie tematów z bazy Z DODANIEM NUMERACJI
        if self.storage:
            topics_rows = self.storage.get_topics(exam_id=exam_data["id"])
            for idx, t in enumerate(topics_rows, 1):
                self.txt_topics.insert("end", f"{idx}. {t['name']}\n")

        # --- DODANA AUTOMATYCZNA NUMERACJA ---
        def on_focus(event):
            if not self.txt_topics.get("1.0", "end-1c").strip():
                self.txt_topics.insert("1.0", "1. ")

        def on_enter(event):
            line_start = self.txt_topics.index("insert linestart")
            line_end = self.txt_topics.index("insert lineend")
            current_line = self.txt_topics.get(line_start, line_end)

            match = re.match(r"^(\d+)\.\s*(.*)", current_line)
            if match:
                if not match.group(2).strip():
                    self.txt_topics.delete(line_start, line_end)
                    return "break"
                next_num = int(match.group(1)) + 1
                self.txt_topics.insert("insert", f"\n{next_num}. ")
                return "break"
            return None

        self.txt_topics.bind("<FocusIn>", on_focus)
        self.txt_topics.bind("<Return>", on_enter)
        # ------------------------------------

        # PRZYCISKI
        btn_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        btn_frame.grid(row=9, column=0, columnspan=2, pady=10)

        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save_changes"], command=self.save_changes,
                                 **self.btn_style)
        btn_save.pack(side="left", padx=10)

        btn_delete = ctk.CTkButton(btn_frame, text=self.txt["btn_delete"], command=self.delete_exam, **self.btn_style)
        btn_delete.pack(side="left", padx=10)
        btn_delete.configure(fg_color="#e74c3c", hover_color="#c0392b")

        btn_cancel = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.perform_close, **self.btn_style)
        btn_cancel.pack(side="left", padx=10)
        btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

    def perform_close(self):
        if self.close_callback:
            self.close_callback()
        elif hasattr(self, 'winfo_toplevel'):
            try:
                self.winfo_toplevel().destroy()
            except:
                pass

    def open_semester_menu(self):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=self.txt.get("val_all", "All"),
                         command=lambda: self.filter_subjects_by_semester(None))
        menu.add_separator()
        sorted_semesters = sorted(self.semesters, key=lambda x: (not x["is_current"], x["start_date"]), reverse=True)
        for sem in sorted_semesters:
            label_text = sem["name"]
            if sem["is_current"]: label_text += f" ({self.txt.get('tag_current', 'Current')})"
            menu.add_command(label=label_text, command=lambda s_id=sem["id"]: self.filter_subjects_by_semester(s_id))
        try:
            x = self.btn_sem_filter.winfo_rootx()
            y = self.btn_sem_filter.winfo_rooty() + self.btn_sem_filter.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def filter_subjects_by_semester(self, semester_id):
        if semester_id is None:
            filtered_names = [s["name"] for s in self.db_subjects]
        else:
            filtered_names = [s["name"] for s in self.db_subjects if s["semester_id"] == semester_id]
        if not filtered_names: filtered_names = [""]
        self.combo_subject.configure(values=filtered_names)
        current = self.combo_subject.get()
        if current not in filtered_names and filtered_names:
            self.combo_subject.set(filtered_names[0])
        elif current not in filtered_names:
            self.combo_subject.set("")

    def save_changes(self):
        if not self.storage: return
        subject_name = self.combo_subject.get().strip()
        title = self.ent_title.get().strip()
        date_val = self.ent_date.get()
        time_val = self.ent_time.get().strip()

        if not subject_name or not title:
            messagebox.showwarning(self.txt["msg_error"], self.txt.get("msg_fill_fields", "Fill all fields"))
            return

        subject_id = None
        subject_color = self.exam_data.get("color")

        for sub in self.db_subjects:
            if sub["name"] == subject_name:
                subject_id = sub["id"]
                subject_color = sub["color"]
                break

        if not subject_id:
            random_colors = ["#e74c3c", "#8e44ad", "#3498db", "#1abc9c", "#f1c40f", "#e67e22", "#2ecc71"]
            subject_color = random.choice(random_colors)
            semesters = self.storage.get_semesters()
            semester_id = None
            if semesters:
                curr = [s for s in semesters if s["is_current"]]
                semester_id = curr[0]["id"] if curr else semesters[0]["id"]
            else:
                semester_id = f"sem_{uuid.uuid4().hex[:8]}"
                self.storage.add_semester({
                    "id": semester_id, "name": "Default Semester",
                    "start_date": str(datetime.now().date()),
                    "end_date": str((datetime.now() + timedelta(days=180)).date()),
                    "is_current": 1
                })
            subject_id = f"sub_{uuid.uuid4().hex[:8]}"
            short_name = subject_name[:3].upper()
            self.storage.add_subject({
                "id": subject_id, "semester_id": semester_id, "name": subject_name,
                "short_name": short_name, "color": subject_color, "weight": 1.0
            })

        updated_exam = {
            "id": self.exam_data["id"], "subject_id": subject_id, "subject": subject_name,
            "title": title, "date": date_val, "time": time_val, "note": self.exam_data.get("note", ""),
            "ignore_barrier": self.var_ignore_barrier.get(), "color": subject_color
        }
        self.storage.update_exam(updated_exam)

        new_names_lines = []
        for line in self.txt_topics.get("0.0", "end").split("\n"):
            clean_line = re.sub(r"^\d+\.\s*", "", line.strip())
            if clean_line:
                new_names_lines.append(clean_line)
        current_db_topics = self.storage.get_topics(self.exam_data["id"])
        existing_map = {t["name"]: dict(t) for t in current_db_topics}
        kept_ids = []

        for name in new_names_lines:
            if name in existing_map:
                kept_ids.append(existing_map[name]["id"])
            else:
                new_id = f"topic_{uuid.uuid4().hex[:8]}"
                new_topic = {
                    "id": new_id, "exam_id": self.exam_data["id"], "name": name,
                    "status": "todo", "scheduled_date": None, "locked": False, "note": ""
                }
                self.storage.add_topic(new_topic)

        for db_topic in current_db_topics:
            if db_topic["id"] not in kept_ids: self.storage.delete_topic(db_topic["id"])

        self.perform_close()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_data_updated"])
        if self.callback: self.callback()

    def delete_exam(self):
        if not self.storage: return
        confirm = messagebox.askyesno(self.txt["msg_warning"],
                                      self.txt["msg_confirm_del_exam"].format(subject=self.exam_data["subject"]))
        if confirm:
            self.storage.delete_exam(self.exam_data["id"])
            self.perform_close()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_deleted"])
            if self.callback: self.callback()


# --- EDYCJA POJEDYNCZEGO TEMATU ---
class EditTopicPanel(ctk.CTkFrame):
    def __init__(self, parent, txt, btn_style, topic_data, callback=None, storage=None, close_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.txt = txt
        self.btn_style = btn_style
        self.topic_data = topic_data
        self.callback = callback
        self.storage = storage
        self.close_callback = close_callback

        # CENTROWANIE
        self.center_box = ctk.CTkFrame(self, fg_color="transparent")
        self.center_box.pack(expand=True, fill="x", padx=30)
        self.center_box.grid_columnconfigure(0, weight=1)
        self.center_box.grid_columnconfigure(1, weight=2)

        # NAGŁÓWEK
        header_title = self.txt["win_edit_topic_title"].format(name=topic_data["name"])
        ctk.CTkLabel(self.center_box, text=header_title, font=("Arial", 18, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                          pady=(10, 5))

        exam_name = "Unknown Exam"
        if self.storage:
            ex = self.storage.get_exam(topic_data["exam_id"])
            if ex: exam_name = f"{ex['subject']} ({ex['title']})"

        ctk.CTkLabel(self.center_box, text=f"Exam: {exam_name}", text_color="gray", font=("Arial", 11)).grid(row=1,
                                                                                                             column=0,
                                                                                                             columnspan=2,
                                                                                                             pady=(0,
                                                                                                                   20))

        ctk.CTkLabel(self.center_box, text=self.txt["form_topic"]).grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.ent_name = ctk.CTkEntry(self.center_box)
        self.ent_name.insert(0, topic_data["name"])
        self.ent_name.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.center_box, text=self.txt["form_date"]).grid(row=3, column=0, padx=10, pady=10, sticky="e")

        date_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        date_frame.grid(row=3, column=1, padx=10, pady=10, sticky="w")
        self.ent_date = DateEntry(date_frame, width=15, date_pattern='y-mm-dd', background='#3a3a3a',
                                  foreground='white', borderwidth=0)
        self.ent_date.pack()

        self.original_date = topic_data.get("scheduled_date", "")
        if self.original_date: self.ent_date.set_date(self.original_date)

        self.is_locked = tk.BooleanVar(value=topic_data.get("locked", False))
        check_locked = ctk.CTkCheckBox(self.center_box, text=self.txt["form_lock"], variable=self.is_locked,
                                       onvalue=True,
                                       offvalue=False)
        check_locked.grid(row=4, column=0, columnspan=2, pady=20)

        btn_frame = ctk.CTkFrame(self.center_box, fg_color="transparent")
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)

        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save"], command=self.save_changes, **self.btn_style)
        btn_save.pack(side="left", padx=10)

        btn_delete = ctk.CTkButton(btn_frame, text=self.txt["btn_delete"], command=self.delete_topic, **self.btn_style)
        btn_delete.pack(side="left", padx=10)
        btn_delete.configure(fg_color="#e74c3c", hover_color="#c0392b")

        btn_cancel = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.perform_close, **self.btn_style)
        btn_cancel.pack(side="left", padx=10)
        btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

    def perform_close(self):
        if self.close_callback:
            self.close_callback()
        elif hasattr(self, 'winfo_toplevel'):
            try:
                self.winfo_toplevel().destroy()
            except:
                pass

    def save_changes(self):
        if not self.storage: return
        new_name = self.ent_name.get()
        new_date = self.ent_date.get()

        if not new_name:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_topic_name_req"])
            return

        updated_topic = dict(self.topic_data)
        updated_topic["name"] = new_name
        if not new_date.strip():
            updated_topic["scheduled_date"] = None
        else:
            updated_topic["scheduled_date"] = new_date
        updated_topic["locked"] = self.is_locked.get()

        infomess = self.txt["btn_refresh"]
        if new_date and str(self.original_date) != new_date:
            updated_topic["locked"] = True
            infomess = self.txt["msg_topic_date_lock"]

        self.storage.update_topic(updated_topic)
        self.perform_close()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_updated"].format(info=infomess))
        if self.callback: self.callback()

    def delete_topic(self):
        if not self.storage: return
        confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_topic"])
        if confirm:
            self.storage.delete_topic(self.topic_data["id"])
            self.perform_close()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_deleted"])
            if self.callback: self.callback()