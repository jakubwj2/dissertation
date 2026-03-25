from models.session import Session
from gui.gui import (
    create_ui_menu,
    create_menu_bar,
    create_tkinter_window,
    create_answer_var,
)


def main():
    session = Session.create()
    root = create_tkinter_window()
    answer_var = create_answer_var(root)
    ui = create_ui_menu(session, answer_var)
    ui.master = root

    menubar = create_menu_bar(session)
    menubar.master = root
    root.config(menu=menubar)

    root.mainloop()


if __name__ == "__main__":
    main()
