import os
from datetime import date, datetime


PATH = os.getcwd()
LOG_PATH = PATH + "\\server_logs\\"

class Logger:
    def __init__(self):
        pass

    def set_log_path(self):
        self.log_name = 