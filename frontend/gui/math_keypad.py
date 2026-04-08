import re
import tkinter as tk
from functools import partial
from typing import Any, Callable

from eventbus import Event, EventEnum, bus

BUTTON_FONT = ("Cascadia Code", 32)


class MathKeypad(tk.Frame):
    def __init__(
        self,
        master,
        target_string_var: tk.StringVar,
    ):
        super().__init__(master)
        self.target_string_var = target_string_var

        self._build()

    def _build(self) -> None:
        self.create_buttons()
        self.position_buttons()

    def create_buttons(self) -> None:
        self.digit_buttons = [self.get_configured_digit_button(i) for i in range(10)]
        self.dot_button = self.get_configured_digit_button(".")
        self.backspace_button = self.get_configured_button(
            "\u232b", self.on_backspace_click
        )
        self.negate_button = self.get_configured_button("+/-", self.on_negate_click)
        self.button_enter = self.get_configured_button("\u21b5", self.on_enter_click)

    def on_enter_click(self) -> None:
        payload = {"answer": float(self.target_string_var.get())}
        bus.publish(Event(EventEnum.SUBMIT_ANSWER, payload))

    def position_buttons(self) -> None:
        grid_config = {"sticky": tk.NSEW, "padx": 1, "pady": 1}

        for i in range(9):
            row, column = i // 3, i % 3
            self.digit_buttons[i + 1].grid(grid_config, row=row, column=column)

        self.digit_buttons[0].grid(grid_config, row=3, column=0, columnspan=2)
        self.dot_button.grid(grid_config, row=3, column=2)

        self.backspace_button.grid(grid_config, row=0, column=3)
        self.negate_button.grid(grid_config, row=1, column=3)
        self.button_enter.grid(grid_config, row=2, column=3, rowspan=2)

        self.grid_rowconfigure(tk.ALL, uniform="buttons", weight=1)
        self.grid_columnconfigure(tk.ALL, uniform="buttons", weight=1)

    def get_configured_button(
        self, label: Any, command: Callable[[], None]
    ) -> tk.Button:
        return tk.Button(self, text=str(label), command=command, font=BUTTON_FONT)

    def get_configured_digit_button(self, digit: Any) -> tk.Button:
        command = partial(self.on_grid_button_click, digit)
        return self.get_configured_button(digit, command)

    def on_grid_button_click(self, digit: str) -> None:
        if digit == ".":
            if "." in self.target_string_var.get():
                return

        elif self.target_string_var.get() == "0":
            self.target_string_var.set(digit)
            return

        self.target_string_var.set(self.target_string_var.get() + str(digit))

    def on_negate_click(self) -> None:
        if re.match(r"^[0\.]*$", self.target_string_var.get()):
            return

        if self.target_string_var.get().startswith("-"):
            self.target_string_var.set(self.target_string_var.get()[1:])
        else:
            self.target_string_var.set("-" + self.target_string_var.get())

    def on_backspace_click(self) -> None:
        self.target_string_var.set(self.target_string_var.get()[:-1])

        if (
            len(self.target_string_var.get()) == 0
            or self.target_string_var.get() == "-"
        ):
            self.target_string_var.set("0")

        if re.match(r"^-[0\.]*$", self.target_string_var.get()):
            self.target_string_var.set(self.target_string_var.get()[1:])
