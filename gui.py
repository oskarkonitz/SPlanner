import tkinter as tk
from tkinter import messagebox
from storage import load, save
from planner import plan
import uuid

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Planer Nauki v1.0")
        self.root.geometry("400x400")

        self.data = load()
        print(f"Loaded exams: {len(self.data["exams"])}")

        self.label_title = tk.Label(self.root, text="Planer Nauki", font=("Arial", 20, "bold"))
        self.label_title.pack(pady=20)
        self.btn_add = tk.Button(self.root, text="Dodaj Egzamin", width=20, height=2, command=self.add_window)
        self.btn_add.pack(pady=10)
        self.btn_plan = tk.Button(self.root, text="Generuj Plan", width=20, height=2, command=self.run_planner)
        self.btn_plan.pack(pady=10)
        self.btn_week = tk.Button(self.root, text="Pokaż Tydzień", width=20, height=2, command=self.show_week)
        self.btn_week.pack(pady=10)
        self.btn_exit = tk.Button(self.root, text="Wyjście", width=20, height=2, command=self.root.quit)
        self.btn_exit.pack(pady=20)

    def run_planner(self):
        try:
            plan(self.data)
            save(self.data)
            messagebox.showinfo("Sukces", "Planowanie zakonczone")
        except Exception as e:
            messagebox.showerror("Error", e)

    def add_window(self):
        messagebox.showinfo("fds", "Fsd")

    def show_week(self):
        messagebox.showinfo("abc", "def")



if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()