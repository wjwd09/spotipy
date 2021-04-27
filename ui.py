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
from kivy.uix.progressbar import ProgressBar
import uuid
import threading
from time import sleep
from kivy.clock import Clock
import queue as Queue 
import json
from functools import partial
import datetime
import pickle

red = [1, 0, 0, 1] 
green = [0, 1, 0, 1] 
blue = [0, 0, 1, 1]  

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
            btn1.bind(on_release=partial(self.song_pressed, (f"{track}-{self.results[track]['artist']}",self.results[track]['uri'])))

            widg.add_widget(btn1)

    def song_pressed(self, uri, *args):
        track_info = {}
        track_info["name"] = uri[0]
        track_info["uri"] = uri[1]
        App.get_running_app().client.send("ADD_TO_QUEUE", "Server", json.dumps(track_info))

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
            permission_grid = GridLayout(cols = 5)
            user_label = Label(text = self.results[i]["display_name"])
            permission_grid.add_widget(user_label)
            for permission in self.results[i]["permissions"].keys():
                btn = Button(size_hint = (0.17,0.17))
                btn.text = f"{permission}"
                if self.results[i]['permissions'][permission]:
                    btn.background_color=green
                else:
                    btn.background_color=red
                btn.bind(on_release= partial(self.user_pressed, i, permission, btn))
                btn.disabled = not host
                permission_grid.add_widget(btn)

            
            grid.add_widget(permission_grid)

    def user_pressed(self, user_id, permission,btn, *args):
        App.get_running_app().client.change_permission(user_id,permission)
        if btn.background_color == red:
            btn.background_color= green
        else:
            btn.background_color= red

    def clear_results(self):
        self.grid_l.clear_widgets()
                
class QueueWindow(Screen):
    grid_l = ObjectProperty(None)
    top_lbl = ObjectProperty(None)
    queue = []
    permission = True
    queue_options = ["MOVE_UP", "MOVE_DOWN", "DELETE"]

    def show_queue(self):
        
        self.clear_results()
        grid = self.grid_l
        grid.bind(minimum_height=grid.setter('height'),
                     minimum_width=grid.setter('width'))
        
        for song in range(len(self.queue)):
            
            song_grid = GridLayout(cols = 4)
            song_lbl = Label(text=self.queue[song][0], color = green)
            song_grid.add_widget(song_lbl)
            for i in range(3):
                btn = Button(size_hint=(0.25,0.25))
                btn.text = self.queue_options[i]
                btn.bind(on_release=partial(self.handle_queue_update, song, self.queue_options[i]))
                btn.disabled = not self.permission
                song_grid.add_widget(btn)
            grid.add_widget(song_grid)

    def handle_queue_update(self, btn, action, *args):
        queue_info = {}
        queue_info["song_index"] = btn
        queue_info["action"] = action
        App.get_running_app().client.send("QUEUE_UPDATE", "Server", json.dumps(queue_info))
    
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
        self.red = red
        self.green = green
        self.blue = blue
        return kv

    def print_something(self, command):
        Logger.info("{}".format(command))

    def start_clock(self):
        self.update = Clock.schedule_interval(lambda dt: self.periodic_update(),0.5)
        #self.ask_for_song = Clock.schedule_interval(lambda dt: self.ask_song(),5)

    def ask_song(self):
        self.client.send("GET_CURRENT_SONG", "Server", "CURRENT_SONG")


    def periodic_update(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get()
                self.print_something(msg)
                if type(msg) != type(10):
                
                    if msg["HEADER"] == "SESSION_ID":
                        kv.get_screen("main").ids.session_id_text.text = msg["MESSAGE"]

                    elif msg["HEADER"] == "SESSION_INFO":
                        message = json.loads(msg["MESSAGE"])
                        kv.get_screen("main").ids.session_id_text.text = message["session_id"]
                        kv.get_screen("users").ids.lblID.text = message["host"] + "'s session"
                    elif msg["HEADER"] == "CURRENT_SONG":
                        song_data = json.loads(msg["MESSAGE"])
                        kv.get_screen("main").ids.current_song_text.text = song_data["name"] +"-"+ song_data["artist"]
                        kv.get_screen("main").ids.song_progress.max = song_data["runtime"]
                        kv.get_screen("main").ids.song_progress.value = song_data["progress"]
                        kv.get_screen("main").ids.song_progress_text.text = convert_ms(song_data["progress"])
                        kv.get_screen("main").ids.song_duration_text.text = convert_ms(song_data["runtime"])
                    elif msg["HEADER"] == "USERS":
                        users = json.loads(msg["MESSAGE"])
                        self.print_something(users)

                        kv.get_screen("users").results = users
                        kv.get_screen("users").grid_l.clear_widgets()
                        kv.get_screen("users").show_users(self.host)

                    elif msg["MESSAGE"] == "PLEASE START SPOTIFY":
                        kv.get_screen("main").ids.current_song_text.text = "Please Start SPOTIFY"

                    elif msg["HEADER"] == "SEARCH_RESULTS":
                        kv.get_screen("search").results = json.loads(msg["MESSAGE"])
                        kv.get_screen("search").search_pressed()

                    elif msg["HEADER"] == "QUEUE_UPDATE":
                        kv.get_screen("queue").queue = json.loads(msg["MESSAGE"])
                        kv.get_screen("queue").show_queue()

                    elif msg["HEADER"] == "PERMISSION_UPDATE":
                        message = json.loads(msg["MESSAGE"])
                        
                        if message["permission"] == "playback":
                            kv.get_screen("main").ids.playback.disabled = not message["value"]
                        elif message["permission"] == "skip":
                            kv.get_screen("main").ids.skip_forward.disabled = not message["value"]
                            kv.get_screen("main").ids.skip_back.disabled = not message["value"]
                        elif message["permission"] == "add_to_queue":
                            kv.get_screen("main").ids.search_btn.disabled = not message["value"]
                        elif message["permission"] == "edit_queue":
                            kv.get_screen("queue").permission = not kv.get_screen("queue").permission
                            


                    elif msg["HEADER"] == "FAILURE":
                        self.print_something(msg["MESSAGE"])

                    elif msg["HEADER"] == "!DISCONNECT":
                        self.client.close_client()
                        self.ask_for_song.cancel()
                        self.update.cancel()
                        self.client = Client(self.queue)

                    return True
            except:
                Logger.info("oops")

        self.queue.queue.clear()
        return True
    
def convert_ms(ms):
    sec = int(ms/1000)
    return str(datetime.timedelta(seconds = sec))
      
    

if __name__ == "__main__":
    MyMainApp().run()