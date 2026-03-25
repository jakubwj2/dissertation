import tkinter as tk


def on_grid_button_click(digit: str, var: tk.StringVar):
    if digit == ".":
        if "." in var.get():
            return

    elif var.get() == "0":
        var.set(digit)
        return

    var.set(var.get() + str(digit))


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
