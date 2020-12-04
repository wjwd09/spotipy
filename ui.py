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
from threaded_client import Client
from kivy.logger import Logger
from kivy.properties import StringProperty
import uuid
import threading
from time import sleep
from kivy.clock import Clock
import queue as Queue 

class MainWindow(Screen):
    session_id_text = StringProperty("")

class StartWindow(Screen):
    pass

class CreateWindow(Screen):
    pass

class JoinWindow(Screen):
    pass

class SearchWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

kv = Builder.load_file("my.kv")
Logger.info("command = {}".format(kv.screens[3].ids.session_id_text.text))
Logger.info("command = {}".format(kv.get_screen("main").ids.session_id_text.text))
Logger.info("command = {}".format(kv.screens))

class MyMainApp(App):
    def build(self):
        self.queue = Queue.Queue()
        self.client = Client(self.queue)
        Clock.schedule_interval(lambda dt: self.periodic_update(),1)
        self.kv = kv
        return kv

    def print_something(self, command):
        Logger.info("command = {}".format(command))

    def periodic_update(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get()
                kv.get_screen("main").ids.session_id_text.text = msg
                self.print_something(msg)
            except Queue.Empty:
                pass
    

    

if __name__ == "__main__":
    MyMainApp().run()