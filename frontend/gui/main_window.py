from __future__ import annotations

import tkinter as tk

from eventbus import Event, EventEnum, bus
from gui.math_keypad import MathKeypad
from gui.menu_bar import MenuBar
from models.question import Question
from services.session import Session


class MainWindow:
    text_font = ("Cascadia Code", 20)

    def __init__(self, session: Session):
        self.session = session

        self.root = tk.Tk(
            screenName=None, baseName=None, className="Smart Tutor", useTk=True
        )
        self.question_var = tk.StringVar(value="13 + 17 =")
        self.answer_var = tk.StringVar(value="0")
        self.feedback_var = tk.StringVar(value="Answer to get started!")

    @classmethod
    def create(cls, session: Session) -> MainWindow:
        instance = MainWindow(session)

        menubar = MenuBar(instance.root, session)

        instance.populate_tkinter_window()
        ui = MathKeypad(instance.root, instance.answer_var)
        ui.pack(fill=tk.BOTH, expand=True)

        bus.subscribe(EventEnum.PROBLEM_LOGGED, instance.on_problem_logged)
        bus.subscribe(EventEnum.QUESTION_RECEIVED, instance.on_question_received)
        return instance

    def run(self):
        self.session.client.get_current_model()
        self.root.mainloop()

    def on_question_received(self, event: Event):
        question = Question.from_dict(event.payload["question"])
        self.question_var.set(question.text)
        self.answer_var.set("0")

    def on_problem_logged(self, event: Event):
        correct = event.payload["correct"]
        response_time = event.payload["response_time"]

        correct_str = "Correct" if correct else "Incorrect"
        self.feedback_label.config(fg="green" if correct else "red")
        self.feedback_var.set(f"{correct_str}! ({response_time:.2f}s)")

    def populate_tkinter_window(self):
        self.root.title("Smart Tutor")
        self.root.geometry("300x400")
        self.root.option_add("*tearOff", False)

        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        label_config = {"master": top_frame, "font": MainWindow.text_font}

        question_label = tk.Label(textvariable=self.question_var, **label_config)
        answer_label = tk.Label(textvariable=self.answer_var, **label_config)
        self.feedback_label = tk.Label(textvariable=self.feedback_var, **label_config)

        self.feedback_label.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        question_label.pack(fill=tk.BOTH, side=tk.LEFT)
        answer_label.pack(fill=tk.BOTH, side=tk.RIGHT)
