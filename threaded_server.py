import socket
import threading
import json
import random, string

PREFIX = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
HEADERS = ["CTS", "CTC", "INIT"]

class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind(ADDR)
        self.connections = {}
        self.sessions = {}



    def handle_client(self,conn,addr):
        print(f"[NEW CONNECTION] {addr} connected")

        connected = True
        while connected:
            try:
                msg_length = conn.recv(PREFIX).decode(FORMAT)
            except Exception as ex:
                print(str(ex))

            if msg_length:
                msg_length = int(msg_length)
                raw_msg = conn.recv(msg_length).decode(FORMAT)
                message = json.loads(raw_msg)

                if message["HEADER"] == DISCONNECT_MESSAGE:
                    connected = False
                
                elif message["HEADER"] == "CREATE":
                    session_id = "".join(random.choices(string.ascii_letters + string.digits, k = 4))
                    indentifer = json.loads(message["MESSAGE"])
                    self.sessions[session_id] = {
                        "HOST" : {
                            "ID"            : message["ID"],
                            "NAME"          : indentifer["display_name"], 
                            "spotify_user"  : indentifer["spotify_user"],
                            "spotify_pass"  : indentifer["spotify_pass"]
                        },
                        "USERS" : {}
                    }
                    print(self.sessions) 
                
                elif message["HEADER"] == "JOIN":
                    msg = json.loads(message["MESSAGE"])
                    session_id = msg["session_id"]
                    if session_id in self.sessions.keys():
                        self.sessions[session_id]["USERS"][message["ID"]] = {
                            "display_name"  : msg["display_name"],
                            "permissions"   : {}   
                        } 
                    print(self.sessions)
                else:
                    print("None")

        print(self.sessions)
        print(f"[CLOSING CONNECTION] {addr} closed")
        conn.close()

    def create_message(self, header, dest, sender, msg):
        if header in HEADERS:
            message = {
                "HEADER"    : f"{header}",
                "DEST"      : f"{dest}",
                "SENDER"    : f"{sender}",
                "MESSAGE"   : f"{msg}"
            }
            return message
        else:
            return None

    def send(self,header,dest,sender,msg):
        if sender in self.connections.keys():
            message = self.create_message(header,dest,sender,msg)

            if message == None:
                print("Not a valid Message")
            else:
                message = json.dumps(message)
                message = message.encode(FORMAT)
                msg_len = len(message)
                send_length = str(msg_len).encode(FORMAT)
                send_length += b' ' * (PREFIX-len(send_length))

                conn = self.connections[dest]["CONN"]
                conn.send(message)
        else:
            conn = self.connections[sender]["CONN"]
            conn.send("User DNE").encode(FORMAT)



    def start(self):
        self.server.listen()
        print(f"[STARTING] server is starting\nListening on {SERVER}:{PORT}")
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target = self.handle_client, args = (conn,addr))
            thread.start()

if __name__ == "__main__":
    server = Server()
    server.start()
