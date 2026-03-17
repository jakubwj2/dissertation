import tkinter as tk
from functools import partial


def on_grid_button_click(digit: str, var: tk.StringVar):
    if digit == ".":
        if "." in var.get():
            return

    elif var.get() == "0":
        var.set(digit)
        return

    var.set(var.get() + str(digit))


def on_enter_click(var: tk.StringVar):
    pass


def on_negate_click(var: tk.StringVar):
    if var.get().count("0") + var.get().count(".") == len(var.get()):
        return

    if var.get().startswith("-"):
        var.set(var.get()[1:])
    else:
        var.set("-" + var.get())


def on_backspace_click(var: tk.StringVar):
    var.set(var.get()[:-1])

    if len(var.get()) == 0 or var.get() == "-":
        var.set("0")


NUMBER_FONT = ("Cascadia Code", 32)


root = tk.Tk(screenName=None, baseName=None, className="Smart Tutor", useTk=True)
root.title("Smart Tutor")
root.geometry("300x400")

question_label = tk.Label(root, text="What is 13 + 17?", font=("Cascadia Code", 20))
question_label.pack(fill=tk.X, expand=True)

answer_var = tk.StringVar(value="0")
answer_label = tk.Label(
    root,
    textvariable=answer_var,
    font=NUMBER_FONT,
)
answer_label.pack(fill=tk.X, expand=True)


grid_frame = tk.Frame(root)
grid_frame.pack(fill=tk.BOTH, expand=True)

button_config = {
    "master": grid_frame,
    "font": NUMBER_FONT,
}

grid_config = {
    "sticky": tk.NSEW,
    "padx": 1,
    "pady": 1,
}

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
    text="0", command=partial(on_grid_button_click, "0", answer_var), **button_config
)
zero_button.grid(row=3, column=0, columnspan=2, **grid_config)

dot_button = tk.Button(
    text=".", command=partial(on_grid_button_click, ".", answer_var), **button_config
)
dot_button.grid(row=3, column=2, **grid_config)

backspace_button = tk.Button(
    text="\u232b", command=partial(on_backspace_click, answer_var), **button_config
)
backspace_button.grid(row=0, column=3, **grid_config)

negate_button = tk.Button(
    # \u207A\u2215\u208B
    text="+/-", command=partial(on_negate_click, answer_var), **button_config
)
negate_button.grid(row=1, column=3, **grid_config)

button_enter = tk.Button(
    # \u21B5, \u23CE, \21A9
    text="\u21b5",
    command=partial(on_enter_click, answer_var),
    **button_config,
)
button_enter.grid(row=2, column=3, rowspan=2, **grid_config)


grid_frame.grid_rowconfigure(tk.ALL, uniform="buttons", weight=1)
grid_frame.grid_columnconfigure(tk.ALL, uniform="buttons", weight=1)

if __name__ == "__main__":
    root.mainloop()
