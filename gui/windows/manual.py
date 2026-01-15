import tkinter as tk

class ManualWindow:
    def __init__(self, parent, txt, btn_style):
        self.win = tk.Toplevel(parent)
        self.win.title(txt["manual_title"])
        self.win.geometry("600x500")

        frame = tk.Frame(self.win)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text = tk.Text(frame, wrap="word", yscrollcommand=scrollbar.set, padx=10, pady=10)
        text.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=text.yview)

        text.tag_config("bold", font=("Arial", 20, "bold"))
        text.tag_config("normal", font=("Arial", 13))

        text.insert("end", txt["manual_header"], "bold")
        text.insert("end", txt["manual_content"], "normal")
        text.configure(state="disabled")
        btn_close = tk.Button(self.win, text=txt["btn_close"], command=self.win.destroy, **btn_style,
                              activeforeground="red")
        btn_close.pack(side="bottom", pady=10)