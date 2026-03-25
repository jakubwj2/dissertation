import tkinter as tk
from functools import partial


from models.session import Session
from models.question import Question
from models.user import User
from gui.math_buttons import on_grid_button_click, on_backspace_click, on_negate_click
from api.api_client import client


class GUI:
    text_font = ("Cascadia Code", 20)
    button_font = ("Cascadia Code", 32)

    def __init__(self, session: Session):
        self.session = Session
        self.root = tk.Tk(
            screenName=None, baseName=None, className="Smart Tutor", useTk=True
        )
        self.question_var = tk.StringVar(value="13 + 17 =")
        self.answer_var = tk.StringVar(value="0")
        self.feedback_var = tk.StringVar(value="Answer to get started!")

    @classmethod
    def create(cls, session: Session) -> "GUI":
        gui = GUI(session)

        gui.populate_tkinter_window()
        ui = gui.create_ui_menu(session)
        ui.master = gui.root

        menubar = gui.create_menu_bar(session)
        menubar.master = gui.root
        gui.root.config(menu=menubar)
        return gui

    def run(self):
        self.root.mainloop()

    def on_start_question(self, question: Question):
        self.question_var.set(question.text)
        self.answer_var.set("0")

    def on_answered(self, correct: bool, response_time: float):
        correct_str = "Correct" if correct else "Incorrect"
        self.feedback_label.config(fg="green" if correct else "red")
        self.feedback_var.set(f"{correct_str}! ({response_time:.2f}s)")

    def populate_tkinter_window(self):
        self.root.title("Smart Tutor")
        self.root.geometry("300x400")
        self.root.option_add("*tearOff", False)

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        label_config = {"master": top_frame, "font": GUI.text_font}

        question_label = tk.Label(textvariable=self.question_var, **label_config)
        answer_label = tk.Label(textvariable=self.answer_var, **label_config)
        self.feedback_label = tk.Label(textvariable=self.feedback_var, **label_config)

        self.feedback_label.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        question_label.pack(fill=tk.BOTH, side=tk.LEFT)
        answer_label.pack(fill=tk.BOTH, side=tk.RIGHT)

    def create_ui_menu(self, session: Session) -> tk.Frame:
        grid_frame = tk.Frame()
        grid_frame.pack(fill=tk.BOTH, expand=True)

        button_config = {"master": grid_frame, "font": GUI.button_font}

        grid_config = {"sticky": tk.NSEW, "padx": 1, "pady": 1}

        for i in range(9):
            row, column = i // 3, i % 3
            digit = str(i + 1)
            digit_button = tk.Button(
                text=digit,
                command=partial(on_grid_button_click, digit, self.answer_var),
                **button_config,
            )
            digit_button.grid(row=row, column=column, **grid_config)

        zero_button = tk.Button(
            text="0",
            command=partial(on_grid_button_click, "0", self.answer_var),
            **button_config,
        )
        zero_button.grid(row=3, column=0, columnspan=2, **grid_config)

        dot_button = tk.Button(
            text=".",
            command=partial(on_grid_button_click, ".", self.answer_var),
            **button_config,
        )
        dot_button.grid(row=3, column=2, **grid_config)

        backspace_button = tk.Button(
            text="\u232b",
            command=partial(on_backspace_click, self.answer_var),
            **button_config,
        )
        backspace_button.grid(row=0, column=3, **grid_config)

        negate_button = tk.Button(
            text="+/-",
            command=partial(on_negate_click, self.answer_var),
            **button_config,
        )
        negate_button.grid(row=1, column=3, **grid_config)

        def on_enter_click():
            session.process_answer(
                float(self.answer_var.get()), self.on_answered, self.on_start_question
            )

        button_enter = tk.Button(
            # \u21B5, \u23CE, \21A9
            text="\u21b5",
            command=on_enter_click,
            **button_config,
        )
        button_enter.grid(row=2, column=3, rowspan=2, **grid_config)

        grid_frame.grid_rowconfigure(tk.ALL, uniform="buttons", weight=1)
        grid_frame.grid_columnconfigure(tk.ALL, uniform="buttons", weight=1)
        return grid_frame

    def create_menu_bar(self, session: Session) -> tk.Menu:
        menubar = tk.Menu()

        menu_user = tk.Menu(menubar, tearoff=0)

        menubar.add_cascade(menu=menu_user, label="User")

        menu_user.add_command(
            label="Create User",
            command=partial(session.on_debug_create_user, self.on_start_question),
        )
        menu_user.add_command(label="Get User", command=session.on_get_user)

        menu_select_user = tk.Menu(menu_user, tearoff=0)

        def user_select_callback(users: list[dict]):
            menu_select_user.delete(0, tk.END)
            for user_json in users:
                user_json["user_type"]
                menu_select_user.add_command(
                    label=f"User {user_json['username']}",
                    command=partial(
                        session.set_user,
                        User.from_dict(user_json),
                        self.on_start_question,
                    ),
                )

        client.get_users(user_select_callback)

        menu_user.add_cascade(menu=menu_select_user, label="Select User")
        menu_user.add_command(
            label="Refresh Users", command=partial(client.get_users, user_select_callback)
        )

        session.get_recommended_exercise(self.on_start_question)
        menubar.add_command(label="Visualize", command=session.on_visualize)
        return menubar
