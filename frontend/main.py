import logging
import os


from models.session import Session
from gui.gui import GUI


def main():
    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s (%(asctime)s) [%(levelname)s]: %(message)s",
        handlers=[logging.FileHandler("logs/app.log"), logging.StreamHandler()],
    )

    session = Session.create()

    gui = GUI.create(session)
    gui.run()


if __name__ == "__main__":
    main()
