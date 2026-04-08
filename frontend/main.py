import logging
import os

from gui.main_window import MainWindow
from services.session import Session
from utils.main_thread_dispatcher import MainThreadDispatcher


def main():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging.basicConfig(
        level=logging.INFO,
        format='%(name)s (%(asctime)s) [%(levelname)s] "%(message)s"',
        handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
    )

    main_thread_dispatcher = MainThreadDispatcher()
    session = Session.create(main_thread_dispatcher)

    gui = MainWindow.create(session, main_thread_dispatcher)
    gui.run()


if __name__ == "__main__":
    main()
