import tkinter as tk
from functools import partial


from models.session import Session
from gui.math_buttons import on_grid_button_click, on_backspace_click, on_negate_click
from api.api_client import get_users


NUMBER_FONT = ("Cascadia Code", 32)


def create_tkinter_window() -> tk.Tk:
    root = tk.Tk(screenName=None, baseName=None, className="Smart Tutor", useTk=True)
    root.title("Smart Tutor")
    root.geometry("300x400")
    root.option_add("*tearOff", False)


    question_label = tk.Label(root, text="What is 13 + 17?", font=("Cascadia Code", 20))
    question_label.pack(fill=tk.X, expand=True)
    return root


def create_answer_var(root: tk.Tk) -> tk.StringVar:
    answer_var = tk.StringVar(value="0")
    answer_label = tk.Label(root, textvariable=answer_var, font=NUMBER_FONT)
    answer_label.pack(fill=tk.X, expand=True)
    return answer_var


def create_ui_menu(session: Session, answer_var: tk.StringVar) -> tk.Frame:
    grid_frame = tk.Frame()
    grid_frame.pack(fill=tk.BOTH, expand=True)

    button_config = {"master": grid_frame, "font": NUMBER_FONT}

    grid_config = {"sticky": tk.NSEW, "padx": 1, "pady": 1}

    for i in range(9):
        row, column = i // 3, i % 3
        digit = str(i + 1)
        digit_button = tk.Button(
            text=digit,
            command=partial(on_grid_button_click, digit, answer_var),
            **button_config,
        )
        digit_button.grid(row=row, column=column, **grid_config)

    zero_button = tk.Button(
        text="0",
        command=partial(on_grid_button_click, "0", answer_var),
        **button_config,
    )
    zero_button.grid(row=3, column=0, columnspan=2, **grid_config)

    dot_button = tk.Button(
        text=".",
        command=partial(on_grid_button_click, ".", answer_var),
        **button_config,
    )
    dot_button.grid(row=3, column=2, **grid_config)

    backspace_button = tk.Button(
        text="\u232b", command=partial(on_backspace_click, answer_var), **button_config
    )
    backspace_button.grid(row=0, column=3, **grid_config)

    negate_button = tk.Button(
        text="+/-",
        command=partial(on_negate_click, answer_var),
        **button_config,
    )
    negate_button.grid(row=1, column=3, **grid_config)

    button_enter = tk.Button(
        # \u21B5, \u23CE, \21A9
        text="\u21b5",
        command=partial(session.process_answer, answer_var),
        **button_config,
    )
    button_enter.grid(row=2, column=3, rowspan=2, **grid_config)

    grid_frame.grid_rowconfigure(tk.ALL, uniform="buttons", weight=1)
    grid_frame.grid_columnconfigure(tk.ALL, uniform="buttons", weight=1)
    return grid_frame


def create_menu_bar(session: Session) -> tk.Menu:
    menubar = tk.Menu()

    menu_user = tk.Menu(menubar, tearoff=0)

    menubar.add_cascade(menu=menu_user, label="User")

    menu_user.add_command(label="Create User", command=session.on_debug_create_user)
    menu_user.add_command(label="Get User", command=session.on_get_user)

    menu_select_user = tk.Menu(menu_user, tearoff=0)

    def user_select_callback(users: list[dict]):
        menu_select_user.delete(0, tk.END)
        for user_json in users:
            user_json["user_type"]
            menu_select_user.add_command(
                label=f"User {user_json['username']}",
                command=partial(session.set_user, user_json),
            )

    get_users(user_select_callback)

    menu_user.add_cascade(menu=menu_select_user, label="Select User")
    menu_user.add_command(
        label="Refresh Users", command=partial(get_users, user_select_callback)
    )

    session.get_recommended_exercise()
    menubar.add_command(label="Visualize", command=session.on_visualize)
    return menubar
