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
    widg_id = ObjectProperty(None)
    results = {}
    def search_pressed(self):
        widg = self.widg_id
        self.clear_results()
        #grid.bind(minimum_height=grid.setter('height'),
        #             minimum_width=grid.setter('width'))

        for track in self.results.keys():
            btn1 = Button(size_hint_y=None)
            btn1.text = track + " - " + self.results[track]['artist']
            btn1.bind(on_release=partial(self.song_pressed, self.results[track]['uri']))

            widg.add_widget(btn1)

    def song_pressed(self, uri, *args):
        App.get_running_app().client.send("ADD_TO_QUEUE", "Server", uri)

    def clear_results(self):
        self.widg_id.clear_widgets()
        
    # pass

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
                btn.bind(on_release= partial(self.user_pressed, i, permission, btn))
                dropdown.add_widget(btn)

            btn1 = Button(size_hint=(1, None))
            btn1.text = self.results[i]["display_name"]
            btn1.bind(on_release=dropdown.open)
            btn1.disabled = not host
            grid.add_widget(btn1)

    def user_pressed(self, user_id, permission,btn, *args):
        App.get_running_app().client.change_permission(user_id,permission)
        if btn.text == f"{permission}:False":
            btn.text = f"{permission}:True"
        else:
            btn.text = f"{permission}:False"

    def clear_results(self):
        self.grid_l.clear_widgets()
                



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
        Clock.schedule_interval(lambda dt: self.periodic_update(),0.5)
        Clock.schedule_interval(lambda dt: self.ask_song(),5)

    def ask_song(self):
        self.client.send("GET_CURRENT_SONG", "Server", "CURRENT_SONG")


    def periodic_update(self):
        

        while self.queue.qsize():
            try:
                msg = self.queue.get()
                #self.print_something(msg)
                
                if msg["HEADER"] == "SESSION_ID":
                    message = json.loads(msg["MESSAGE"])
                    kv.get_screen("main").ids.session_id_text.text = message["session_id"]
                    kv.get_screen("users").ids.lblID.text = message["host"] + "'s session"
                elif msg["HEADER"] == "CURRENT_SONG":
                    song_data = json.loads(msg["MESSAGE"])
                    kv.get_screen("main").ids.current_song_text.text = song_data["name"]
                elif msg["HEADER"] == "USERS":
                    users = json.loads(msg["MESSAGE"])

                    #self.print_something(users)

                    self.print_something(users)

                    kv.get_screen("users").results = users
                    kv.get_screen("users").grid_l.clear_widgets()
                    kv.get_screen("users").show_users(self.host)



                    kv.get_screen("users").results = users
                    kv.get_screen("users").grid_l.clear_widgets()
                    kv.get_screen("users").show_users(self.host)


                    kv.get_screen("users").results = list(users)
                    kv.get_screen("users").search_btn_pressed()

                elif msg["MESSAGE"] == "PLEASE START SPOTIFY":
                    kv.get_screen("main").ids.current_song_text.text = "Please Start SPOTIFY"

                elif msg["HEADER"] == "SEARCH_RESULTS":
                    kv.get_screen("search").results = json.loads(msg["MESSAGE"])
                    kv.get_screen("search").search_pressed()

                elif msg["HEADER"] == "PERMISSION_UPDATE":
                    message = json.loads(msg["MESSAGE"])
                    self.print_something(message)
                    if message["permission"] == "playback":
                        kv.get_screen("main").ids.playback.disabled = not message["value"]
                    elif message["permission"] == "skip":
                        kv.get_screen("main").ids.skip_forward.disabled = not message["value"]
                        kv.get_screen("main").ids.skip_back.disabled = not message["value"]
                    elif message["permission"] == "add_to_queue":
                        kv.get_screen("main").ids.search_btn.disabled = not message["value"]

                elif msg["HEADER"] == "FAILURE":
                    self.print_something(msg["MESSAGE"])

                return True
            except:
                return True

        self.queue.queue.clear()
        return True
    

    

if __name__ == "__main__":
    MyMainApp().run()