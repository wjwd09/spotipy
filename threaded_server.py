import socket
import threading
import json
import random, string
from time import sleep

PREFIX = 64
PORT = 5060
SERVER = ''
#SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
HEADERS = ["CTS", "CTC", "INIT","RECV","BROADCAST", "BROADCAST_S"]

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
                print(f"[{addr}] DISCONNECTED")
                self.handle_unexpected_disconnect(client_id,conn)
                break

            if msg_length:
                msg_length = int(msg_length)
                try:
                    raw_msg = conn.recv(msg_length).decode(FORMAT)
                except:
                    print(f"[{addr}] DISCONNECTED")
                    self.handle_unexpected_disconnect(client_id,conn)
                    break
                message = json.loads(raw_msg)

                if message["HEADER"] == DISCONNECT_MESSAGE:
                    connected = False
                    self.handle_disconnect(message,conn)
                
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
                    self.connections[message["ID"]] = {
                            "display_name"  : indentifer["display_name"],
                            "session_id"    : session_id,
                            "host"          : True,
                            "CONN"          : conn,
                            "ADDR"          : addr
                    }
                    client_id = message["ID"] 
                
                elif message["HEADER"] == "JOIN":
                    msg = json.loads(message["MESSAGE"])
                    session_id = msg["session_id"]
                    if session_id in self.sessions.keys():
                        self.sessions[session_id]["USERS"][message["ID"]] = {
                            "display_name"  : msg["display_name"],
                            "permissions"   : {}   
                        }
                        self.connections[message["ID"]] = {
                            "display_name"  : msg["display_name"],
                            "session_id"    : session_id,
                            "host"          : False,
                            "CONN"          : conn,
                            "ADDR"          : addr
                        } 
                    client_id = message["ID"]
                elif message["HEADER"] == "BROADCAST_S":
                    session_id = self.connections[message["ID"]]["session_id"]
                    self.broadcast_to_session(session_id,"BROADCAST_S", message["MESSAGE"])
                elif message["HEADER"] == "BROADCAST":
                    self.broadcast_to_all("BROADCAST", message["MESSAGE"])
                else:
                    print(f"[{addr}] {message['MESSAGE']}")
                    self.send("RECV",client_id,f"[MESSAGE RECIEVED]{message['MESSAGE']}")


        print("Thread Closing")

    def print_sessions(self):
        print("[Printing Sessions]")
        for key in self.sessions.keys():
            print(f"{key}:\n\t{self.sessions[key]}")

    def print_connections(self):
        print("[Printing Connections]")
        for key in self.connections.keys():
            print(f"{key}:\n\t{self.connections[key]}")


    def handle_disconnect(self,message,conn):
        if self.connections[message["ID"]]["host"] == True: #if user is host, delete all connections 
            print("HOST DISCONNECTING")
            session_location = self.connections[message["ID"]]["session_id"]
            for key in self.sessions[session_location]["USERS"].keys():
                self.connections[key]["CONN"].send("closed".encode(FORMAT))
                self.connections[key]["CONN"].close() #close each connection
                del self.connections[key] #delete the connection from the connections dictionary
            del self.sessions[session_location] # delete the session
            del self.connections[message["ID"]]
            conn.send("closed".encode(FORMAT))
            conn.close()
        else:
            session_location = self.connections[message["ID"]]["session_id"]
            del self.sessions[session_location]["USERS"][message["ID"]]
            del self.connections[message["ID"]]
            conn.send("closed".encode(FORMAT))
            conn.close()
        
    def handle_unexpected_disconnect(self,client_id, conn):
        try:
            if self.connections[client_id]["host"] == True: #if user is host, delete all connections 
                session_location = self.connections[client_id]["session_id"]
                for key in self.sessions[session_location]["USERS"].keys():
                    self.connections[key]["CONN"].send("closed".encode(FORMAT))#send closed message 
                    self.connections[key]["CONN"].close() #close each connection
                    del self.connections[key] #delete the connection from the connections dictionary
                del self.sessions[session_location] # delete the session
                del self.connections[client_id]
                #conn.send("closed".encode(FORMAT))
                conn.close()
            else:
                session_location = self.connections[client_id]["session_id"]
                del self.sessions[session_location]["USERS"][client_id]
                del self.connections[client_id]
                conn.send("closed".encode(FORMAT))
                conn.close()
        except:
            pass
        

    def create_message(self, header, dest, msg):
        if header in HEADERS:
            message = {
                "HEADER"    : f"{header}",
                "DEST"      : f"{dest}",
                "MESSAGE"   : f"{msg}"
            }
            return message
        else:
            return None

    def send(self,header,dest,msg):
        
        message = self.create_message(header,dest,msg)

        if message == None:
            print("Not a valid Message")
        else:
            message = json.dumps(message)
            message = message.encode(FORMAT)
            msg_len = len(message)
            send_length = str(msg_len).encode(FORMAT)
            send_length += b' ' * (PREFIX-len(send_length))

            conn = self.connections[dest]["CONN"]
            conn.send(send_length)
            conn.send(message)
    
    def broadcast_to_all(self,header,msg):
        for key in self.connections.keys():
            self.send(header,key,msg)

    def broadcast_to_session(self,session_id,header,msg):
        host = self.sessions[session_id]["HOST"]["ID"]
        self.send(header,host,msg)
        for key in self.sessions[session_id]["USERS"].keys():
            self.send(header,key,msg)
        

    def show_connections(self):
        prev_threads = get_num_connections()
        print(f"[Initial Num Threads] {get_num_connections()}")
        while True:
            if get_num_connections() != prev_threads:
                print(f"[CHANGE IN THREADS] Num threads: {get_num_connections()}")
                sleep(0.1)
                self.print_connections()
                self.print_sessions()
                prev_threads = get_num_connections()

    def start(self):
        self.server.listen()
        print(f"[STARTING] server is starting\nListening on {SERVER}:{PORT}")
        connections = threading.Thread(target = self.show_connections)
        connections.start()
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target = self.handle_client, args = (conn,addr))
            thread.start()

def get_num_connections():
    return threading.activeCount()

if __name__ == "__main__":
    server = Server()
    server.start()
