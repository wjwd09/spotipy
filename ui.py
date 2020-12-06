import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition
from kivy.uix.dropdown import DropDown
from threaded_client import Client
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.properties import ListProperty
import uuid
import threading
from time import sleep
from kivy.clock import Clock
import queue as Queue 
import json
from functools import partial

class MainWindow(Screen):
    session_id_text = StringProperty("")
    current_song_text = StringProperty("")

class StartWindow(Screen):
    pass

class CreateWindow(Screen):
    pass

class JoinWindow(Screen):
    pass

class SearchWindow(Screen):
    pass

class UsersWindow(Screen):
    grid_l = ObjectProperty(None)
    top_lbl = ObjectProperty(None)
    results = {}
    def show_users(self, host):
        grid = self.grid_l
        grid.bind(minimum_height=grid.setter('height'),
                     minimum_width=grid.setter('width'))

        for i in self.results.keys():
            Logger.info("{}".format(self.results[i]["display_name"]))
            dropdown = DropDown()
            for permission in self.results[i]["permissions"].keys():
                #Logger.info("{}".format(permission))
                btn = Button(size_hint = (1,None))
                btn.text = f"{permission}:{self.results[i]['permissions'][permission]}"
                #btn.bind(on_release= lambda permission: App.get_running_app().client.change_permission(i,permission))
                dropdown.add_widget(btn)

            btn1 = Button(size_hint=(1, None))
            btn1.text = self.results[i]["display_name"]
            btn1.bind(on_release=dropdown.open)
            btn1.disabled = not host
            grid.add_widget(btn1)
                

<<<<<<< HEAD
                
=======
    def on_pre_enter(self):
        self.search_btn_pressed()
>>>>>>> parent of 0cfee30 (fixed users showing up multiple times)



class WindowManager(ScreenManager):
    pass

kv = Builder.load_file("my.kv")


class MyMainApp(App):
    def build(self):
        self.queue = Queue.Queue()
        self.client = Client(self.queue)
        self.host = False
        self.kv = kv
        return kv

    def print_something(self, command):
        Logger.info("{}".format(command))

    def start_clock(self):
        Clock.schedule_interval(lambda dt: self.periodic_update(),1)

    def periodic_update(self):
        self.client.send("GET_CURRENT_SONG", "Server", "CURRENT_SONG")

        while self.queue.qsize():
            try:
                msg = self.queue.get()
                if msg["HEADER"] == "SESSION_ID":
                    kv.get_screen("main").ids.session_id_text.text = msg["MESSAGE"]
                elif msg["HEADER"] == "CURRENT_SONG":
                    song_data = json.loads(msg["MESSAGE"])
                    kv.get_screen("main").ids.current_song_text.text = song_data["name"]
                elif msg["HEADER"] == "USERS":
                    users = json.loads(msg["MESSAGE"])
                    self.print_something(users)
<<<<<<< HEAD
                    kv.get_screen("users").results = users
                    kv.get_screen("users").grid_l.clear_widgets()
                    kv.get_screen("users").show_users(self.host)
=======
                    kv.get_screen("users").results = list(users)
                    kv.get_screen("users").search_btn_pressed()
>>>>>>> parent of 0cfee30 (fixed users showing up multiple times)
                elif msg["MESSAGE"] == "PLEASE START SPOTIFY":
                    kv.get_screen("main").ids.current_song_text.text = "Please Start SPOTIFY"

                return True
            except:
                return True
        
        return True
    

    

if __name__ == "__main__":
    MyMainApp().run()