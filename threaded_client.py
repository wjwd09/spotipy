import socket
import requests
import json
import uuid
import threading
from time import sleep
from spotifyClient import spotifyClient

#---- Spotipy Client Constants ----
SCOPE = "user-read-playback-state user-modify-playback-state"
CLIENT_ID = "cc9859af7bda4fea8c2e74321becb949"
REDIRECT_URI = "http://localhost:8888/callback"
#----------------------------------

PREFIX = 64
PORT = 25565
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
<<<<<<< HEAD
LOCAL_SERVER = "10.0.0.91"
=======
LOCAL_SERVER = "10.0.0.17"
>>>>>>> 252247f52000542002a3bfa5d2eeb4754571389e
#LOCAL_SERVER = socket.gethostbyname(socket.gethostname())
PUBLIC_SERVER = "68.84.71.235"

LOCAL_ADDR = (LOCAL_SERVER,PORT)
PUBLIC_ADDR = (PUBLIC_SERVER,PORT)

HEADERS = ["CTS", DISCONNECT_MESSAGE, "CREATE", "JOIN","BROADCAST_S", "BROADCAST", "SET_PERMISSION", "PLAYBACK", "SEARCH", "ADD_TO_QUEUE", "GET_CURRENT_SONG","PLAY","REWIND","SKIP","GET_USERS","QUEUE_UPDATE"]

def get_public_ip():
    return str(requests.get('https://api.ipify.org').text)

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
            if PUBLIC_SERVER == get_public_ip():
                self.client.connect(LOCAL_ADDR)
            else:
                self.client.connect(PUBLIC_ADDR)
        except Exception as ex:
            print(str(ex))

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
                try:
                    msg_len = int(msg)
                except:
                    self.queue.put(msg)
                    msg_len = 4096
                try:
                    raw_msg = self.client.recv(msg_len).decode(FORMAT)
                    message = json.loads(raw_msg)
                    self.queue.put(message)
                    if message["HEADER"] == DISCONNECT_MESSAGE:
                        break
                        
                except Exception as ex:
                    self.queue.put(str(ex))

                

            except Exception as ex:
                print(str(ex))
                print("Client closed")
                return

    def set_permissions(self, user_id, permissions):
        return_permissions = {"client_id" : user_id, "permissions" : permissions}
        p = json.dumps(return_permissions)
        self.send("SET_PERMISSIONS", "Server", p)

    def change_permission(self, user_id, permission):
        msg = {}
        msg["client_id"] = user_id
        msg["permission"] = permission
        self.send("SET_PERMISSION", "Server", json.dumps(msg))

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
