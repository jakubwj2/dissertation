from tkinter import Menu, END
from functools import partial
from typing import Callable

from services.session import Session
from models.user import User
from models.question import Question


class MenuBar(Menu):
    def __init__(
        self, master, session: Session, on_start_question: Callable[[Question], None]
    ):
        super().__init__(master, tearoff=0)
        self.session = session
        self.on_start_question = on_start_question

        user_menu = UserBar(self, self.session, self.on_start_question)
        self.add_cascade(menu=user_menu, label="User")

        self.session.get_recommended_exercise(self.on_start_question)
        self.add_command(label="Visualize", command=self.session.on_visualize)


class UserBar(Menu):
    def __init__(
        self, master, session: Session, on_start_question: Callable[[Question], None]
    ):
        super().__init__(master, tearoff=0)
        self.session = session
        self.on_start_question = on_start_question

        self.add_command(
            label="Create User",
            command=partial(self.session.on_debug_create_user, self.on_start_question),
        )
        self.add_command(label="Get User", command=self.session.on_get_user)

        self.menu_select_user = DebugUserSelection(
            self, self.session, self.on_start_question
        )

        self.add_cascade(menu=self.menu_select_user, label="Select User")
        self.add_command(
            label="Refresh Users",
            command=self.menu_select_user.update_users,
        )


class DebugUserSelection(Menu):
    def __init__(
        self, master, session: Session, on_start_question: Callable[[Question], None]
    ):
        super().__init__(master, tearoff=0)
        self.session = session
        self.on_start_question = on_start_question

        self.update_users()

    def update_users(self):
        self.session.get_users(self._update_users_callback)

    def _update_users_callback(self, users: list[dict]):
        self.delete(0, END)
        for user_json in users:
            label = f"{user_json['username']} ({user_json['user_type']})"
            user = User.from_dict(user_json)

            self.add_command(
                label=label,
                command=partial(self.session.set_user, user, self.on_start_question),
            )
