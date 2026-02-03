import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

# Definicje palet kolorów
THEMES = {
    "light": {
        "mode": "Light",
        "bg_root": "#f3f3f3",
        "bg_sidebar": "#f3f3f3",
        "fg_text": "#1a1a1a",

        # Przyciski
        "btn_fg": "#e0e0e0",
        "btn_hover": "#d6d6d6",
        "btn_text": "#1a1a1a",
        "btn_border": "#b0b0b0",

        # Tabela
        "bg_tree": "#ffffff",
        "fg_tree": "#000000",
        "bg_tree_head": "#e5e5e5",
        "fg_tree_head": "#000000",
        "select_bg": "#b0b0b0",
        "select_fg": "#ffffff",

        # DateEntry
        "date_entry_bg": "#ffffff",
        "date_entry_fg": "#000000",
        "date_btn_bg": "#e1e1e1",

        # Zakładki (Tabview)
        "tab_text": "#1a1a1a",
        "tab_fg": "#e0e0e0",
        "tab_btn_fg": "#e0e0e0",
        "tab_btn_hover": "#d6d6d6",
        "tab_btn_selected": "#ffffff",
        "tab_btn_text": "#1a1a1a",
    },
    "dark": {
        "mode": "Dark",
        "bg_root": "#242424",
        "bg_sidebar": "#242424",
        "fg_text": "#e0e0e0",

        # Przyciski
        "btn_fg": "#3a3a3a",
        "btn_hover": "#454545",
        "btn_text": "#ffffff",
        "btn_border": "#3a3a3a",

        # Tabela
        "bg_tree": "#2b2b2b",
        "fg_tree": "#e0e0e0",
        "bg_tree_head": "#3a3a3a",
        "fg_tree_head": "#ffffff",
        "select_bg": "#404040",
        "select_fg": "#ffffff",

        # DateEntry
        "date_entry_bg": "#343638",
        "date_entry_fg": "#ffffff",
        "date_btn_bg": "#4a4a4a",

        # Zakładki (Tabview)
        "tab_text": "#e0e0e0",
        "tab_fg": "#2b2b2b",
        "tab_btn_fg": "#2b2b2b",
        "tab_btn_hover": "#3a3a3a",
        "tab_btn_selected": "#454545",
        "tab_btn_text": "#ffffff",
    }
}


def apply_theme(app, theme_name):
    colors = THEMES.get(theme_name, THEMES["light"])

    # 1. Ustawienie trybu CustomTkinter
    ctk.set_appearance_mode(colors["mode"])
    ctk.set_default_color_theme("blue")

    # 2. Globalna konfiguracja standardowych widżetów Tkinter
    app.root.option_add("*Background", colors["bg_root"])
    app.root.option_add("*Foreground", colors["fg_text"])
    app.root.option_add("*Frame.background", colors["bg_root"])
    app.root.option_add("*Label.background", colors["bg_root"])

    # 3. Konfiguracja Tabeli i Stylów
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Treeview",
                    background=colors["bg_tree"],
                    foreground=colors["fg_tree"],
                    fieldbackground=colors["bg_tree"],
                    font=("Arial", 11),
                    borderwidth=0)

    style.configure("Treeview.Heading",
                    background=colors["bg_tree_head"],
                    foreground=colors["fg_tree_head"],
                    relief="flat")

    style.map("Treeview.Heading",
              background=[("active", colors["bg_tree_head"]), ("pressed", colors["bg_tree_head"])],
              foreground=[("active", colors["fg_tree_head"]), ("pressed", colors["fg_tree_head"])])

    style.map("Treeview",
              background=[("selected", colors["select_bg"])],
              foreground=[("selected", colors["select_fg"])])

    # DateEntry styles
    style.configure("TEntry", fieldbackground=colors["date_entry_bg"], foreground=colors["date_entry_fg"])
    style.map("TEntry", fieldbackground=[("readonly", colors["date_entry_bg"])],
              foreground=[("readonly", colors["date_entry_fg"])])
    style.configure("TButton", background=colors["date_btn_bg"])

    # 4. Aktualizacja kontenerów głównych
    if hasattr(app, 'root'):
        app.root.configure(bg=colors["bg_root"])

    frames = ['sidebar', 'middle_frame', 'stats_frame', 'plan_container']
    for frame_name in frames:
        if hasattr(app, frame_name):
            widget = getattr(app, frame_name)
            if isinstance(widget, ctk.CTkFrame):
                widget.configure(fg_color=colors["bg_root"])
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=colors["bg_root"])

    # 5. Aktualizacja Labeli w sidebarze
    if hasattr(app, 'sidebar'):
        for widget in app.sidebar.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=colors["bg_root"], fg=colors["fg_text"])
        if hasattr(app, 'stats_frame'):
            for widget in app.stats_frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.configure(bg=colors["bg_root"])
                    if str(widget.cget("foreground")) in ["black", "#000000", "#e0e0e0", "#1a1a1a", "#1a1a1a"]:
                        widget.configure(fg=colors["fg_text"])

    # 6. Przyciski
    if hasattr(app, 'btn_style'):
        app.btn_style["fg_color"] = colors["btn_fg"]
        app.btn_style["text_color"] = colors["btn_text"]
        app.btn_style["hover_color"] = colors["btn_hover"]
        app.btn_style["border_color"] = colors["btn_border"]
        app.btn_style["border_width"] = 1

    main_buttons = ['btn_status', 'btn_edit', 'btn_exit', 'btn_add']
    for btn_name in main_buttons:
        if hasattr(app, btn_name):
            btn = getattr(app, btn_name)
            if isinstance(btn, ctk.CTkButton):
                btn.configure(
                    fg_color=colors["btn_fg"],
                    text_color=colors["btn_text"],
                    hover_color=colors["btn_hover"],
                    border_color=colors["btn_border"],
                    border_width=1
                )

    if theme_name == "light":
        app.root.option_add("*CTkLabel.text_color", colors["fg_text"])
    else:
        app.root.option_add("*CTkLabel.text_color", colors["fg_text"])

        # 7. Tagi w tabeli
    if hasattr(app, 'plan_view') and hasattr(app.plan_view, 'tree'):
        tree = app.plan_view.tree
        tags_basic = ["todo", "normal", "date_header"]
        for tag in tags_basic:
            tree.tag_configure(tag, foreground=colors["fg_tree"])

        tree.tag_configure("today", foreground="violet")
        tree.tag_configure("red", foreground="#ff007f")
        tree.tag_configure("orange", foreground="orange")

        yellow_col = "#e6b800" if theme_name == "light" else "yellow"
        tree.tag_configure("yellow", foreground=yellow_col)

        tree.tag_configure("done", foreground="#00b800")
        tree.tag_configure("exam", foreground="#ff4444")

        if theme_name == "dark":
            tree.tag_configure("overdue", foreground="#888888")
        else:
            tree.tag_configure("overdue", foreground="#555555")

    # 8. Konfiguracja Tabview (Zakładek)
    if hasattr(app, 'tabview'):
        app.tabview.configure(
            fg_color=colors["bg_root"],
            segmented_button_fg_color=colors["tab_fg"],
            segmented_button_selected_color=colors["tab_btn_selected"],
            segmented_button_unselected_color=colors["tab_btn_fg"],
            segmented_button_selected_hover_color=colors["tab_btn_hover"],
            segmented_button_unselected_hover_color=colors["tab_btn_hover"],
            text_color=colors["tab_text"]
        )

    # 9. Placeholder (Empty State) Background - FIX TŁA
    # Ustawiamy tło labela na kolor tła tabeli (bg_tree), żeby się zlało
    if hasattr(app, 'plan_view') and hasattr(app.plan_view, 'lbl_empty'):
        app.plan_view.lbl_empty.configure(fg_color=colors["bg_tree"])

    if hasattr(app, 'todo_view') and hasattr(app.todo_view, 'lbl_empty'):
        app.todo_view.lbl_empty.configure(fg_color=colors["bg_tree"])