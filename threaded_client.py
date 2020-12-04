import socket
import json
import uuid
import threading
import ctypes
from time import sleep
from spotifyClient import spotifyClient

#---- Spotipy Client Constants ----
SCOPE = "user-read-playback-state user-modify-playback-state"
CLIENT_ID = "cc9859af7bda4fea8c2e74321becb949"
REDIRECT_URI = "http://localhost:8888/callback"
#----------------------------------

PREFIX = 64
PORT = 5060
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
LOCAL_SERVER = "10.0.0.17"
#LOCAL_SERVER = socket.gethostbyname(socket.gethostname())
PUBLIC_SERVER = "127.0.0.1"
#PUBLIC_SERVER = "68.84.71.235"
LOCAL_ADDR = (LOCAL_SERVER,PORT)

PUBLIC_ADDR = (PUBLIC_SERVER,PORT)

HEADERS = ["CTS", DISCONNECT_MESSAGE, "CREATE", "JOIN","BROADCAST_S", "BROADCAST", "SET_PERMISSIONS", "PLAYBACK", "SEARCH", "GET_CURRENT_SONG","PLAY","REWIND","SKIP","GET_USERS"]

class Client:
    def __init__(self, queue = None):
        self.name = ""
        self.session_id = ""
        self.queue = queue
        self.id = str(uuid.uuid4())
        self.spotify_Client = None
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.local = False
        
        self.connected = True
        self.recieving = False

    def set_name(self, name):
        self.name = name

    def connect_to_server(self):
        try:
            self.client.connect(PUBLIC_ADDR)
        except:
            self.local = True

        if self.local:
            try:
                self.client.connect(LOCAL_ADDR)
            except Exception as ex:
                print(str(ex))
                return
        
        self.receiver = threading.Thread(target=self.recv_msg)
        self.receiver.start()
        self.connected = True
        self.recieving = False

    def create_session(self):
        msg = {
            "display_name"  : f"{self.name}",
            "spotify_token"  : f"{json.dumps(self.spotify_Client.accTokenDict)}"
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
                    self.queue.put(message)
                        
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

    def search(self, track_name):
        self.send("SEARCH", "Server", track_name)

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

    def spotifySetup(self):
        self.spotify_Client = spotifyClient(clientID=CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
        self.spotify_Client.authSetup()
        self.spotify_Client.getAccToken(getDict=True)

if __name__ == "__main__":
    name = input("enter your name")
    join = input("Create or join")


    if(join == "c"):
        client = Client()
        client.spotifySetup()
        client.set_name(name)
        client.connect_to_server()
        client.create_session()

    elif(join == "j"):
        session_id = input("what session do you want to join")
        client = Client()
        client.set_name(name)
        client.connect_to_server()
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
