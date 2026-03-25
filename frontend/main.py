from models.session import Session
from gui.gui import GUI

def main():
    session = Session.create()
    
    gui = GUI.create(session)
    gui.run()


if __name__ == "__main__":
    main()
