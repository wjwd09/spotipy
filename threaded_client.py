import socket
import json
import uuid
import threading
import ctypes
from time import sleep

PREFIX = 64
PORT = 5060
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
#SERVER = "10.0.0.18"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)

HEADERS = ["CTS", DISCONNECT_MESSAGE, "CREATE", "JOIN","BROADCAST_S", "BROADCAST", "SET_PERMISSIONS"]

class Client:
    def __init__(self, name, id, spotify_user="",spotify_pass=""):
        self.name = name
        self.id = id
        self.spotify_user = spotify_user
        self.spotify_pass = spotify_pass
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client.connect(ADDR)
        self.receiver = threading.Thread(target=self.recv_msg)
        self.receiver.start()
        self.connected = True
        self.recieving = False

    def create_session(self):
        msg = {
            "display_name"  : f"{self.name}",
            "spotify_user"  : f"{self.spotify_user}",
            "spotify_pass"  : f"{self.spotify_pass}",
        }
        msg = json.dumps(msg)
        self.send("CREATE", "Server", msg)

    def join_session(self, session_id):
        msg = {
            "session_id"    : session_id,
            "display_name"  : f"{self.name}"
        }
        msg = json.dumps(msg)
        self.send("JOIN", "Server", msg)

    def create_disconnect_message(self):
        return self.create_message(DISCONNECT_MESSAGE, "Server", DISCONNECT_MESSAGE)

    def recv_msg(self):
        while True:
            try:
                msg = self.client.recv(PREFIX).decode(FORMAT)
                msg_len = int(msg)
                try:
                    raw_msg = self.client.recv(msg_len).decode(FORMAT)
                    message = json.loads(raw_msg)
                    if message["HEADER"] == DISCONNECT_MESSAGE:
                        print(message["MESSAGE"])
                        ctypes.windll.user32.MessageBoxW(0, message["MESSAGE"], str(self.name), 1)
                        self.close_client()
                        break
                    elif message["HEADER"] == "USER_JOINED":
                        # self.recieving = True
                        # user_permissions = self.set_permissions(message["MESSAGE"])
                        # self.send("SET_PERMISSIONS", "Server", user_permissions)
                        # self.recieving = False
                        pass
                    else:
                        print(message["MESSAGE"])
                        ctypes.windll.user32.MessageBoxW(0, message["MESSAGE"], str(self.name), 1)
                except:
                    print(f"[SERVER NOT RESPONDING] closing client")
                    self.close_client()
                    break

            except Exception as ex:
                print(str(ex))
                print("Client closed")
                return

    def set_permissions(self, user_id):
        permissions = {}
        permissions["add_to_queue"] = input("Should this user be allowed to add to the queue?[T/F] ")
        permissions["remove_from_queue"] = input("Should this user be allowed to remove from the queue?[T/F] ")
        permissions["pause"] = input("Should this user be allowed to pause playback?[T/F] ")
        permissions["play"] = input("Should this user be allowed to play?[T/F] ")
        permissions["skip"] = input("Should this user be allowed to skip?[T/F] ")
        for key in permissions.keys():
            print(permissions[key])
            if permissions[key] == 'T' or permissions[key] == 't':
                permissions[key] = True
            else:
                permissions[key] = False
            print(permissions[key])
        permissions = json.dumps(permissions)
        return_permissions = {"client_id" : user_id, "permissions" : permissions}
        return json.dumps(return_permissions)

    def close_client(self):
        self.client.close()
        self.connected = False


    def create_message(self, header, dest, msg):
        if header in HEADERS:
            message = {
                "HEADER"    : f"{header}",
                "DEST"      : f"{dest}",
                "ID"        : f"{self.id}",
                "MESSAGE"   : f"{msg}"
            }
            return message
        else:
            return None



    def send(self,header,dest,msg):
        if msg == DISCONNECT_MESSAGE:
            message = self.create_disconnect_message()
        else:
            message = self.create_message(header,dest,msg)

        if message == None:
            print("Not a valid Message")
        else:
            message = json.dumps(message)
            message = message.encode(FORMAT)
            msg_len = len(message)
            send_length = str(msg_len).encode(FORMAT)
            send_length += b' ' * (PREFIX-len(send_length))

            self.client.send(send_length)
            self.client.send(message)

if __name__ == "__main__":
    name = input("enter your name")
    join = input("Create or join")


    if(join == "c"):
        client = Client(name, str(uuid.uuid4()))
        client.create_session()

    elif(join == "j"):
        session_id = input("what session do you want to join")
        client = Client(name, str(uuid.uuid4()))
        client.join_session(session_id)

    while True:
        header = input("What kind of header")
        dest = input("who do you want to send to")
        msg = input("What message do you want to send")
        if client.connected:
            client.send(header, dest, msg)
        if header == DISCONNECT_MESSAGE:
            break

    print("closing client")
    del client
    exit()
