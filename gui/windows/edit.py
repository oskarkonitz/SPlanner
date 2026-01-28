import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkcalendar import DateEntry
import uuid
from core.storage import save

# funkcja sprawdzajaca czy zaznaczony element jest egzaminem czy tematem
def select_edit_item(parent, data, txt, tree, btn_style, callback=None):
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showinfo(txt["msg_info"], txt["msg_select_edit"])
        return

    item_id = selected_item[0]

    # sprawdzenie czy to egzamin
    for exam in data["exams"]:
        if exam["id"] == item_id:
            EditExamWindow(parent, txt, data, btn_style, exam, callback)
            return

    # sprawdzenie czy to temat
    for topic in data["topics"]:
        if topic["id"] == item_id:
            EditTopicWindow(parent, txt, data, btn_style, topic, callback)
            return

    # blad
    messagebox.showerror(txt["msg_error"], txt["msg_cant_edit"])

# edycja egzaminow
class EditExamWindow():
    def __init__(self, parent, txt, data, btn_style, exam_data, callback=None):
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.exam_data = exam_data
        self.callback = callback

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

        ctk.CTkLabel(self.win, text=self.txt["form_topics_edit"]).grid(row=3, column=0, pady=5, columnspan=2)
        self.txt_topics = tk.Text(self.win, width=40, height=10)
        self.txt_topics.grid(row=4, column=0, columnspan=2, padx=10)

        # wczytanie tematow do pola tekstowego
        self.topics_list = [t for t in self.data["topics"] if t["exam_id"] == exam_data["id"]]
        for t in self.topics_list:
            self.txt_topics.insert(tk.END, t["name"] + "\n")

        #przyciski
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        btn_save = ctk.CTkButton(btn_frame, text=self.txt["btn_save_changes"], command=self.save_changes, **self.btn_style)
        btn_save.pack(side="left", padx=5)
        btn_delete = ctk.CTkButton(btn_frame, text=self.txt["btn_delete"], command=self.delete_exam, **self.btn_style)
        btn_delete.pack(side="left", padx=5)
        btn_delete.configure(fg_color="#e74c3c", hover_color="#c0392b")
        btn_cancel = ctk.CTkButton(btn_frame, text=self.txt["btn_cancel"], command=self.win.destroy, **self.btn_style)
        btn_cancel.pack(side="left", padx=5)
        btn_cancel.configure(fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))

    def save_changes(self):
        # aktualizacja egzaminu
        self.exam_data["subject"] = self.ent_subject.get()
        self.exam_data["date"] = self.ent_date.get()
        self.exam_data["title"] = self.ent_title.get()

        # aktualizacja tematow
        new_names = [line.strip() for line in self.txt_topics.get("1.0", tk.END).split("\n") if line.strip()]
        existing_map = {t["name"]: t for t in self.topics_list}

        topics_keep_ids = []

        for name in new_names:
            if name in existing_map:
                topic = existing_map[name]
                topics_keep_ids.append(topic["id"])
            else:
                new_id = f"topic_{uuid.uuid4().hex[:8]}"
                self.data["topics"].append({
                    "id": new_id,
                    "exam_id": self.exam_data["id"],
                    "name": name,
                    "status": "todo",
                    "scheduled_date": None,
                    "locked": False
                })
                topics_keep_ids.append(new_id)

        # usuniecie rzeczy ktore zniknely z pola tekstowego
        self.data["topics"] = [
            t for t in self.data["topics"]
            if t["exam_id"] != self.exam_data["id"] or t["id"] in topics_keep_ids
        ]

        save(self.data)

        # callback dla odswiezenia widoku
        if self.callback:
            self.callback()

        self.win.destroy()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_data_updated"])

    def delete_exam(self):
        confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_exam"].format(subject=self.exam_data["subject"]))
        if confirm:
            self.data["topics"] = [t for t in self.data["topics"] if t["exam_id"] != self.exam_data["id"]]
            self.data["exams"] = [e for e in self.data["exams"] if e["id"] != self.exam_data["id"]]

            save(self.data)

            # callback dla odswiezenia
            if self.callback:
                self.callback()

            self.win.destroy()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_exam_deleted"])

class EditTopicWindow:
    def __init__(self, parent, txt, data, btn_style, topic_data, callback=None):
        self.txt = txt
        self.data = data
        self.btn_style = btn_style
        self.topic_data = topic_data
        self.callback = callback

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

        #przyciski
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
        new_name = self.ent_name.get()
        new_date = self.ent_date.get()

        if not new_name:
            messagebox.showwarning(self.txt["msg_error"], self.txt["msg_topic_name_req"])
            return

        self.topic_data["name"] = new_name

        if not new_date.strip():
            self.topic_data["scheduled_date"] = None
        else:
            self.topic_data["scheduled_date"] = new_date

        self.topic_data["locked"] = self.is_locked.get()

        infomess = self.txt["btn_refresh"]

        # jesli data zmieniona recznie to blokuje aby generowanie planu nie zmienilo jej
        if new_date and str(self.original_date) != new_date:
            self.topic_data["locked"] = True
            infomess = self.txt["msg_topic_date_lock"]

        save(self.data)

        #callback dla odswiezenia
        if self.callback:
            self.callback()

        self.win.destroy()
        messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_updated"].format(info=infomess))

    def delete_topic(self):
        confirm = messagebox.askyesno(self.txt["msg_warning"], self.txt["msg_confirm_del_topic"])
        if confirm:
            self.data["topics"] = [t for t in self.data["topics"] if t["id"] != self.topic_data["id"]]
            save(self.data)

            # callback dla odswiezenia
            if self.callback:
                self.callback()

            self.win.destroy()
            messagebox.showinfo(self.txt["msg_success"], self.txt["msg_topic_deleted"])