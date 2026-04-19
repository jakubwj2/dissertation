from functools import partial
from tkinter import END, Button, Frame, Label, Menu, Menubutton

from eventbus import Event, EventEnum, bus
from gui.auth_popup import open_auth_popup
from services.session import Session


class MenuBar(Frame):
    def __init__(self, master, session: Session):
        bg_color = "#d9d9d9"
        super().__init__(master, bg=bg_color, height=40, bd=1, relief="raised")
        self.pack(fill="x", side="top")
        self.pack_propagate(False)
        self.session = session

        shared_cnf = {
            "bg": bg_color,
            "padx": 2,
            "pady": 4,
        }

        button_cnf = shared_cnf | {
            "relief": "flat",
            "activebackground": "#ececec",
            "compound": "center",
            "cursor": "hand2",
        }

        menu_pack = {"side": "left", "fill": "y"}
        user_btn = Menubutton(self, button_cnf, text="User")
        user_menu = UserBar(user_btn, self.session)
        user_btn.config(menu=user_menu)
        user_btn.pack(menu_pack)

        model_btn = Menubutton(self, button_cnf, text="Model")
        model_menu = ModelBar(model_btn, self.session)
        model_btn.config(menu=model_menu)
        model_btn.pack(menu_pack)

        visualize_button = Button(
            self,
            button_cnf,
            text="Visualize",
            command=self.session.on_visualize,
        )
        visualize_button.pack(menu_pack)

        self.user_label = Label(self, shared_cnf, text="User")
        self.user_label.pack(side="right")
        self.model_label = Label(self, shared_cnf, text="Model")
        self.model_label.pack(side="right")

        bus.subscribe(EventEnum.MODEL_SELECTED, self.on_model_changed)
        bus.subscribe(EventEnum.USER_LOGGED_IN, self.on_user_logged_in)
        bus.subscribe(EventEnum.USER_LOGGED_OUT, self.on_user_logged_out)
        bus.subscribe(EventEnum.USER_DATA_RECEIVED, self.on_user_data_received)
        bus.subscribe(EventEnum.CURRENT_MODEL_RECEIVED, self.on_model_changed)

    def set_model_label(self, model_name: str, dataset_name: str):
        # self.model_label.config(text=f"{model_name} ({dataset_name})")
        self.model_label.config(text=f"{model_name}")

    def set_user_label(self, username: str, user_type: str):
        # self.user_label.config(text=f"{username} ({user_type})")
        self.user_label.config(text=f"{username}")

    def on_model_changed(self, event: Event):
        self.set_model_label(event.payload["model_name"], event.payload["dataset_name"])

    def on_user_logged_in(self, event: Event):
        self.session.client.get_user()

    def on_user_logged_out(self, event: Event):
        self.set_user_label("", "")

    def on_user_data_received(self, event: Event):
        self.set_user_label(event.payload["username"], event.payload["user_type"])


class UserBar(Menu):
    def __init__(self, master, session: Session):
        super().__init__(master, tearoff=0)
        self.session = session

        if self.session.client.logged_in:
            self.on_user_logged_in(None)
        else:
            self.on_user_logged_out(None)

        bus.subscribe(EventEnum.USER_LOGGED_IN, self.on_user_logged_in)
        bus.subscribe(EventEnum.USER_LOGGED_OUT, self.on_user_logged_out)

    def on_user_logged_in(self, _: Event | None):
        self.delete(0, END)
        self.add_command(label="Logout", command=self.session.logout)

    def on_user_logged_out(self, _: Event | None):
        self.delete(0, END)
        self.add_command(label="Login", command=self.on_login_command)
        self.add_command(label="Register", command=self.on_register_command)

    def on_login_command(self):
        open_auth_popup(self.master, self.session, "login")

    def on_register_command(self):
        open_auth_popup(self.master, self.session, "register")


class ModelBar(Menu):
    def __init__(self, master, session: Session):
        super().__init__(master, tearoff=0)
        self.session = session

        bus.subscribe(EventEnum.MODELS_RECEIVED, self.on_models_received)
        self.session.client.get_models()

        self.add_command(label="Refresh Models", command=self.session.client.get_models)

    def on_models_received(self, event: Event):
        models = event.payload["models"]
        model_hierarchy = {}
        for model in models:
            if model["model_name"] not in model_hierarchy:
                model_hierarchy[model["model_name"]] = []
            model_hierarchy[model["model_name"]].append(model["dataset_name"])

        self.delete(0, END)
        for model_name in model_hierarchy:
            model_menu = Menu(self.master, tearoff=0)
            self.add_cascade(menu=model_menu, label=model_name)
            for dataset_name in model_hierarchy[model_name]:
                payload = {"model_name": model_name, "dataset_name": dataset_name}
                model_menu.add_command(
                    label=dataset_name,
                    command=partial(self.session.client.select_model, payload),
                )
