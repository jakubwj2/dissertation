import tkinter as tk
from tkinter import messagebox

from shared.user_type import UserType, user_type_parser

from eventbus import Event, EventEnum, bus
from services.session import Session


def open_auth_popup(root, session: Session, mode="login"):
    popup = tk.Toplevel(root)
    popup.title("Login" if mode == "login" else "Register")
    popup.geometry("300x250")
    popup.resizable(False, False)
    popup.transient(root)  # keep on top of main window
    popup.grab_set()  # make it modal

    tk.Label(popup, text="Username").pack(pady=(15, 5))
    username_entry = tk.Entry(popup)
    username_entry.pack()

    tk.Label(popup, text="Password").pack(pady=(10, 5))
    password_entry = tk.Entry(popup, show="*")
    password_entry.pack()

    selected = tk.StringVar(value=UserType.STUDENT.value)
    if mode == "register":
        user_type_menu = tk.OptionMenu(popup, selected, *[t for t in UserType])
        user_type_menu.pack()

    def on_user_logged_in(event: Event):
        popup.destroy()

    def on_user_registered(event: Event):
        bus.unsubscribe(EventEnum.USER_LOGGED_IN, on_user_logged_in)
        bus.unsubscribe(EventEnum.USER_REGISTERED, on_user_registered)
        open_auth_popup(root, session, "login")
        popup.destroy()

    bus.subscribe(EventEnum.USER_LOGGED_IN, on_user_logged_in)
    bus.subscribe(EventEnum.USER_REGISTERED, on_user_registered)

    def submit():
        username = username_entry.get().strip()
        password = password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        if mode == "register":
            user_type = user_type_parser(selected.get())
            session.register(username, password, user_type)

        else:  # login
            session.login(username, password)

    tk.Button(
        popup, text="Login" if mode == "login" else "Register", command=submit
    ).pack(pady=15)

    username_entry.focus()
