from __future__ import annotations
import tkinter as tk

from services.session import Session
from models.question import Question
from gui.menu_bar import MenuBar
from gui.math_keypad import MathKeypad


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

        menubar = MenuBar(instance.root, session, instance.on_start_question)
        
        instance.populate_tkinter_window()
        ui = MathKeypad(instance.root, instance.answer_var, instance.on_enter_click)
        ui.pack(fill=tk.BOTH, expand=True)

        return instance

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

        label_config = {"master": top_frame, "font": MainWindow.text_font}

        question_label = tk.Label(textvariable=self.question_var, **label_config)
        answer_label = tk.Label(textvariable=self.answer_var, **label_config)
        self.feedback_label = tk.Label(textvariable=self.feedback_var, **label_config)

        self.feedback_label.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        question_label.pack(fill=tk.BOTH, side=tk.LEFT)
        answer_label.pack(fill=tk.BOTH, side=tk.RIGHT)

    def on_enter_click(self):
        self.session.process_answer(
            float(self.answer_var.get()), self.on_answered, self.on_start_question
        )
