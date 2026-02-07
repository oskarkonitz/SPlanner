import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
import uuid
from gui.windows.color_picker import ColorPickerWindow


# funkcja sprawdzajaca czy zaznaczony element jest egzaminem czy tematem
def select_edit_item(parent, txt, tree, btn_style, callback=None, storage=None):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showinfo(txt["msg_info"], txt["msg_select_edit"])
        return

    item_id = selected_item[0]

    if not storage:
        messagebox.showerror(txt["msg_error"], "StorageManager is missing!")
        return

    # Sprawdzenie czy to egzamin (Szybki SQL)
    target_exam = storage.get_exam(item_id)

    if target_exam:
        # Typy boolean są już naprawione w get_exam()
        EditExamWindow(parent, txt, btn_style, target_exam, callback, storage)
        return

    # Sprawdzenie czy to temat (Szybki SQL)
    target_topic = storage.get_topic(item_id)

    if target_topic:
        # Typy boolean są już naprawione w get_topic()
        EditTopicWindow(parent, txt, btn_style, target_topic, callback, storage)
        return

    # Jeśli nie znaleziono
    messagebox.showerror(txt["msg_error"], txt["msg_cant_edit"])


# edycja egzaminow
class EditExamWindow:
    def __init__(self, parent, txt, btn_style, exam_data, callback=None, storage=None):
        self.txt = txt
        self.btn_style = btn_style
        self.exam_data = exam_data
        self.callback = callback
        self.storage = storage

        # ustawienie okna
        self.win = ctk.CTkToplevel(parent)
        self.win.resizable(False, False)
        self.win.title(self.txt["win_edit_exam_title"].format(subject=exam_data["subject"]))

        # ustawienie pól entry data
        ctk.CTkLabel(self.win, text=self.txt["form_subject"]).grid(row=0, column=0, pady=5, padx=10, sticky="e")
        self.ent_subject = tk.Entry(self.win, width=30)
        self.ent_subject.insert(0, exam_data["subject"])
        self.ent_subject.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(self.win, text=self.txt["form_type"]).grid(row=1, column=0, pady=5, padx=10, sticky="e")
        self.ent_title = tk.Entry(self.win, width=30)
        self.ent_title.insert(0, exam_data["title"])
        self.ent_title.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(self.win, text=self.txt["form_date"]).grid(row=2, column=0, pady=5, padx=10, sticky="e")
        self.ent_date = DateEntry(self.win, width=27, date_pattern='y-mm-dd')
        self.ent_date.grid(row=2, column=1, padx=10, pady=5)
        if exam_data["date"]:
            self.ent_date.set_date(exam_data["date"])

        # Checkbox Ignoruj w planowaniu (Bariera)
        self.var_ignore_barrier = tk.BooleanVar(value=exam_data.get("ignore_barrier", False))
        cb_text = self.txt.get("form_ignore_barrier", "Ignoruj w planowaniu (Bariera)")
        self.cb_barrier = tk.Checkbutton(self.win, text=cb_text, variable=self.var_ignore_barrier,
                                         onvalue=True, offvalue=False)
        self.cb_barrier.grid(row=3, column=0, columnspan=2, pady=(10, 5))

        # Ustalamy domyślny kolor
        self.selected_color = exam_data.get("color")

        # Wizualizacja koloru przycisku
        if self.selected_color:
            btn_visual_color = self.selected_color
        else:
            mode = ctk.get_appearance_mode()
            btn_visual_color = "#000000" if mode == "Light" else "#ffffff"

        color_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        color_frame.grid(row=4, column=0, columnspan=2, pady=(5, 15))

        tk.Label(color_frame, text=self.txt.get("lbl_color", "Color:")).pack(side="left", padx=5)
        self.btn_color = ctk.CTkButton(color_frame, text="", width=30, height=30,
                                       fg_color=btn_visual_color,
                                       command=self.open_color_picker)
        self.btn_color.pack(side="left", padx=5)

        ctk.CTkLabel(self.win, text=self.txt["form_topics_edit"]).grid(row=5, column=0, pady=(0, 5), columnspan=2)
        self.txt_topics = tk.Text(self.win, width=40, height=10)
        self.txt_topics.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 10))

        # wczytanie tematow (Pure SQL)
        if self.storage:
            topics_rows = self.storage.get_topics(exam_id=exam_data["id"])
            # Sortujemy tak, jak w notatniku (choć tutaj kolejność zapisu jest dowolna, w edycji zwykle po nazwie lub dacie)
            # Tutaj po prostu lista
            for t in topics_rows:
                self.txt_topics.insert(tk.END, t["name"] + "\n")

        # przyciski
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)

        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save_changes"], command=self.save_changes,
                                 **self.btn_style)
        btn_save.pack(side="left", padx=5)
        btn_delete = ctk.CTkButton(btn_frame, text=self.txt["btn_delete"], command=self.delete_exam, **self.btn_style)
        btn_delete.pack(side="left", padx=5)
        btn_delete.configure(fg_color="#e74c3c", hover_color="#c0392b")
        btn_cancel = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.win.destroy, **self.btn_style)
        btn_cancel.pack(side="left", padx=5)
        btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

    def open_color_picker(self):
        def on_color_picked(color):
            self.selected_color = color
            self.btn_color.configure(fg_color=color)

        ColorPickerWindow(self.win, self.txt, self.selected_color, on_color_picked)

    def save_changes(self):
        if not self.storage:
            return

        # 1. Update Exam Data
        updated_exam = {
            "id": self.exam_data["id"],
            "subject": self.ent_subject.get(),
            "title": self.ent_title.get(),
            "date": self.ent_date.get(),
            "note": self.exam_data.get("note", ""),
            "ignore_barrier": self.var_ignore_barrier.get(),
            "color": self.selected_color
        }
        self.storage.update_exam(updated_exam)

        # 2. Update Topics
        # Pobieramy listę nazw z pola tekstowego
        new_names_lines = [line.strip() for line in self.txt_topics.get("1.0", tk.END).split("\n") if line.strip()]

        # Pobieramy aktualne tematy z bazy (jako źródło prawdy)
        current_db_topics = self.storage.get_topics(self.exam_data["id"])
        existing_map = {t["name"]: dict(t) for t in current_db_topics}

        # Lista ID, które mają zostać (żeby wiedzieć co usunąć)
        kept_ids = []

        for name in new_names_lines:
            if name in existing_map:
                # Istnieje - zachowujemy
                kept_ids.append(existing_map[name]["id"])
            else:
                # Nowy - dodajemy do bazy
                new_id = f"topic_{uuid.uuid4().hex[:8]}"
                new_topic = {
                    "id": new_id,
                    "exam_id": self.exam_data["id"],
                    "name": name,
                    "status": "todo",
                    "scheduled_date": None,
                    "locked": False,
                    "note": ""
                }
                self.storage.add_topic(new_topic)
                # Nowe dodajemy bez dodawania do kept_ids, bo one nie istnieją w starej bazie

        # Usuwanie: Jeśli temat był w starej bazie, a jego ID nie trafiło na listę zachowanych -> DELETE
        # (Czyli użytkownik usunął linię z tekstem odpowiadającą temu tematowi)
        for db_topic in current_db_topics:
            if db_topic["id"] not in kept_ids:
                self.storage.delete_topic(db_topic["id"])

        self.win.destroy()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_data_updated"])
        if self.callback:
            self.callback()

    def delete_exam(self):
        if not self.storage:
            return

        confirm = messagebox.askyesno(self.txt["msg_warning"],
                                      self.txt["msg_confirm_del_exam"].format(subject=self.exam_data["subject"]))
        if confirm:
            self.storage.delete_exam(self.exam_data["id"])

            self.win.destroy()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_deleted"])
            if self.callback:
                self.callback()


class EditTopicWindow:
    def __init__(self, parent, txt, btn_style, topic_data, callback=None, storage=None):
        self.txt = txt
        self.btn_style = btn_style
        self.topic_data = topic_data
        self.callback = callback
        self.storage = storage

        self.win = tk.Toplevel(parent)
        self.win.title(self.txt["win_edit_topic_title"].format(name=topic_data["name"]))
        self.win.resizable(width=False, height=False)

        ctk.CTkLabel(self.win, text=self.txt["form_topic"]).grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.ent_name = tk.Entry(self.win, width=30)
        self.ent_name.insert(0, topic_data["name"])
        self.ent_name.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(self.win, text=self.txt["form_date"]).grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.ent_date = DateEntry(self.win, width=27, date_pattern='y-mm-dd')
        self.ent_date.grid(row=1, column=1, padx=10, pady=10)

        self.original_date = topic_data.get("scheduled_date", "")
        if self.original_date:
            self.ent_date.set_date(self.original_date)

        self.is_locked = tk.BooleanVar(value=topic_data.get("locked", False))
        check_locked = tk.Checkbutton(self.win, text=self.txt["form_lock"], variable=self.is_locked, onvalue=True,
                                      offvalue=False)
        check_locked.grid(row=2, column=0, columnspan=2, pady=5)

        btn_frame = tk.Frame(self.win)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save"], command=self.save_changes, **self.btn_style)
        btn_save.pack(side="left", padx=5)
        btn_delete = ctk.CTkButton(btn_frame, text=self.txt["btn_delete"], command=self.delete_topic, **self.btn_style)
        btn_delete.pack(side="left", padx=5)
        btn_delete.configure(fg_color="#e74c3c", hover_color="#c0392b")
        btn_cancel = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.win.destroy, **self.btn_style)
        btn_cancel.pack(side="left", padx=5)
        btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

    def save_changes(self):
        if not self.storage:
            return

        new_name = self.ent_name.get()
        new_date = self.ent_date.get()

        if not new_name:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_topic_name_req"])
            return

        # Przygotowanie danych do aktualizacji
        updated_topic = dict(self.topic_data)
        updated_topic["name"] = new_name

        if not new_date.strip():
            updated_topic["scheduled_date"] = None
        else:
            updated_topic["scheduled_date"] = new_date

        updated_topic["locked"] = self.is_locked.get()

        infomess = self.txt["btn_refresh"]
        # Logika blokowania daty przy zmianie
        if new_date and str(self.original_date) != new_date:
            updated_topic["locked"] = True
            infomess = self.txt["msg_topic_date_lock"]

        # Zapis przez StorageManager
        self.storage.update_topic(updated_topic)

        self.win.destroy()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_updated"].format(info=infomess))
        if self.callback:
            self.callback()

    def delete_topic(self):
        if not self.storage:
            return

        confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_topic"])
        if confirm:
            self.storage.delete_topic(self.topic_data["id"])

            self.win.destroy()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_deleted"])
            if self.callback:
                self.callback()