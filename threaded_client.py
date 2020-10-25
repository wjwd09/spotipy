import socket
import json
import uuid
import threading
import ctypes

PREFIX = 64
PORT = 5060
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
#SERVER = "10.0.0.18"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)

HEADERS = ["CTS", DISCONNECT_MESSAGE, "CREATE", "JOIN","BROADCAST_S", "BROADCAST"]

class Client:
    def __init__(self, name, id, spotify_user="",spotify_pass=""):
        self.name = name
        self.id = id
        self.spotify_user = spotify_user
        self.spotify_pass = spotify_pass
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client.connect(ADDR)
        self.reciever = threading.Thread(target=self.recv_msg)
        self.reciever.start()
        self.connected = True


    """ def init_connection(self):
        identifier = {"NAME":self.name, "ID": self.id}
        self.send("INIT", "Server", json.dumps(identifier)) """

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
                if msg == "closed":
                    self.close_client()
                    break
                else:
                    msg_len = int(msg)
                    try:
                        raw_msg = self.client.recv(msg_len).decode(FORMAT)
                        message = json.loads(raw_msg)
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
