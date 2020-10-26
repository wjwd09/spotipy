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
HEADERS = ["CTS", "CTC", "INIT","RECV","BROADCAST", "BROADCAST_S","FAILURE", DISCONNECT_MESSAGE]

class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind(ADDR)
        self.connections = {}
        self.sessions = {}



    def handle_client(self,conn,addr):
        """
        Creates a new while loop thread that handles messages between the client and server
        Parameters      : conn      (socket)    -> Represents the new connection made, used for sending and recieving messages
                        : addr      (str)       -> Represents the ip address and port of the client connection
        Returns         : None
        """
        print(f"[NEW CONNECTION] {addr} connected")
        client_id = ""
        connected = True
        while connected:
            try:
                msg_length = conn.recv(PREFIX).decode(FORMAT)
            except Exception as ex:
                print(f"[{addr}] DISCONNECTED")
                self.handle_unexpected_disconnect(client_id,conn)
                return

            if msg_length:
                msg_length = int(msg_length)
                try:
                    raw_msg = conn.recv(msg_length).decode(FORMAT)
                except:
                    print(f"[{addr}] DISCONNECTED")
                    self.handle_unexpected_disconnect(client_id,conn)
                    return
                message = json.loads(raw_msg)

                if message["HEADER"] == DISCONNECT_MESSAGE:
                    connected = False
                    self.handle_disconnect(message,conn)

                elif message["HEADER"] == "CREATE":
                    session_id = "".join(random.choices(string.ascii_letters + string.digits, k = 4))
                    indentifer = json.loads(message["MESSAGE"])
                    self.create_session(session_id, message["ID"], indentifer["display_name"], indentifer["spotify_user"], indentifer["spotify_pass"])
                    self.add_connection_entry(message["ID"], indentifer["display_name"], session_id, True, conn, addr)
                    client_id = message["ID"]

                elif message["HEADER"] == "JOIN":
                    msg = json.loads(message["MESSAGE"])
                    session_id = msg["session_id"]
                    if session_id in self.sessions.keys():
                        self.add_user_to_session(session_id,message["ID"],msg["display_name"])
                        self.add_connection_entry(message["ID"],msg["display_name"],session_id, False, conn, addr)
                        client_id = message["ID"]
                        self.broadcast_to_session(session_id, "BROADCAST_S", f"[NEW USER HAS JOINED YOUR SESSION] Welcome! {msg['display_name']}", exclude=[client_id])
                    else:
                        self.add_connection_entry(message["ID"],msg["display_name"],session_id, False, conn, addr)
                        self.send("FAILURE", message["ID"], "Session does not exist")
                        self.send(DISCONNECT_MESSAGE,message["ID"],DISCONNECT_MESSAGE)
                        self.delete_connection_entry(message["ID"])
                        break

                elif message["HEADER"] == "BROADCAST_S":
                    session_id = self.connections[message["ID"]]["session_id"]
                    self.broadcast_to_session(session_id,"BROADCAST_S", message["MESSAGE"])
                elif message["HEADER"] == "BROADCAST":
                    self.broadcast_to_all("BROADCAST", message["MESSAGE"])
                else:
                    print(f"[{addr}] {message['MESSAGE']}")
                    self.send("RECV",client_id,f"[MESSAGE RECIEVED]{message['MESSAGE']}")



        print("Thread Closing")

    def handle_disconnect(self,message,conn):
        """
        Handles disconnect message sent from user / host
        Parameters      : message   (dict)      -> Dictionary representation of the message sent to the server
                        : conn      (socket)    -> The connection socket requesting a disconnect
        Returns         : None
        """
        if self.connections[message["ID"]]["host"] == True: #if user is host, delete all connections
            print("HOST DISCONNECTING")
            session_location = self.connections[message["ID"]]["session_id"]
            for key in self.sessions[session_location]["USERS"].keys():
                self.disconnect(self.connections[key]["CONN"]) #close each connection
                self.delete_connection_entry(key) #delete the connection from the connections dictionary
            self.delete_session(session_location) # delete the session
            self.delete_connection_entry(message["ID"])
            self.disconnect(conn)
        else:
            session_location = self.connections[message["ID"]]["session_id"]
            self.delete_session_entry(session_location,message["ID"])
            self.delete_connection_entry(message["ID"])
            self.disconnect(conn)

    def handle_unexpected_disconnect(self,client_id, conn):
        """
        Handles unexpected disconnect from host/user
        Parameters      : client_id     (str)       -> Represents the id of the client that disconnected unexpectedly
                        : conn          (socket)    -> The connection socket that disconnected unexpectedly
        Returns         : None
        """
        try:
            if self.connections[client_id]["host"] == True: #if user is host, delete all connections
                session_location = self.connections[client_id]["session_id"]
                for key in self.sessions[session_location]["USERS"].keys():
                    self.disconnect(self.connections[key]["CONN"]) #close each connection
                    self.delete_connection_entry(key) #delete the connection from the connections dictionary
                self.delete_session(session_location) # delete the session
                self.delete_connection_entry(client_id) # delete the original client entry from connections
                self.disconnect(conn)
            else:
                session_location = self.connections[client_id]["session_id"]
                self.delete_session_entry(session_location,client_id)
                self.delete_connection_entry(client_id)
                self.disconnect(conn)
        except:
            pass




    def send(self,header,dest,msg):
        """
        Sends a message to the specified destination id
        Parameters      : header        (str) -> the header of the message to be sent
                        : dest          (str) -> the client id that the message will be sent to
                        : msg           (str) -> the message to be sent
        """
        message = self.create_message(header,dest,msg)

        if message == None:
            print("Not a valid Message")
        else:
            message = json.dumps(message) # turns message dictionary into json string
            message = message.encode(FORMAT) # encodes message w/ UTF-8
            msg_len = len(message) # gets message length
            send_length = str(msg_len).encode(FORMAT) #encodes message length w/ UTF-8
            send_length += b' ' * (PREFIX-len(send_length)) #pads send length up to 64 bits

            conn = self.connections[dest]["CONN"]
            conn.send(send_length)
            conn.send(message)

    #-----------------------------HELPER FUNCTIONS-----------------------------#
    def create_disconnect_message(self):
        return self.create_message(DISCONNECT_MESSAGE, "Server", DISCONNECT_MESSAGE)

    def disconnect(self,conn):
        """
        Sends a disconnect message to a specified conn object then closes the connection
        Parameters      : conn      (socket)    ->  The connection to be disconnected
        Returns         : None
        """
        discon_msg = self.create_disconnect_message()
        print(discon_msg)
        discon_msg = json.dumps(discon_msg)
        discon_msg = discon_msg.encode(FORMAT)
        discon_len = len(discon_msg)
        discon_len = str(discon_len).encode(FORMAT)
        discon_len += b' ' * (PREFIX-len(discon_msg))
        conn.send(discon_len)
        conn.send(discon_msg)
        conn.close()

    def print_sessions(self):
        """
        Prints all the sessions. Prints the session key, then the host entry followed by all users
        Parameters      : None
        Returns         : None
        """
        print("[Printing Sessions]")
        for key in self.sessions.keys():
            print(f"{key}:\n\t{self.sessions[key]}")

    def print_connections(self):
        """
        Prints all the connections. Prints the user's id, then the user's dictionary entry
        Parameters      : None
        Returns         : None
        """
        print("[Printing Connections]")
        for key in self.connections.keys():
            print(f"{key}:\n\t{self.connections[key]}")

    def get_session_from_user(self, client_id):
        """
        Takes a client ID and returns the session they belong to
        Parameters      : client_id     (str)   -> Represents the id of the client
        Returns         : session_id    (str)   -> Represents the id of the session the client belongs to
        """
        return self.connections[client_id]["session_id"]

    def create_message(self, header, dest, msg):
        """
        Takes a header, message destination, and message. Returns a dictionary of these values
        Parameters      : header        (str)   -> Represents the header of the message
                        : dest          (str)   -> Represents the destination id of the message
                        : msg           (str)   -> Represents the message string to be sent
        Returns         : message       (dict)  -> Dictionary of the parameters
        """
        if header in HEADERS:
            message = {
                "HEADER"    : f"{header}",
                "DEST"      : f"{dest}",
                "MESSAGE"   : f"{msg}"
            }
            return message
        else:
            return None

    def broadcast_to_all(self,header,msg, exclude = []):
        """
        Takes a header and message and sends to all connected clients
        Parameters      : header        (str)   -> Represents the header of the message
                        : msg           (str)   -> Message string to be sent
                        : exclude       (list)  -> A list of string id's that the message will not be sent to
        Returns         : None
        """
        for key in self.connections.keys():
            if key not in exclude:
                self.send(header,key,msg)

    def broadcast_to_session(self,session_id,header,msg, exclude = []):
        """
        Takes a header and message and sends to all connected clients
        Parameters      : session_id    (str)   -> Represents the session id that the message will be broadcast to
                        : header        (str)   -> Represents the header of the message
                        : msg           (str)   -> Message string to be sent
                        : exclude       (list)  -> A list of string id's that the message will not be sent to
        Returns         : None
        """
        host = self.sessions[session_id]["HOST"]["ID"]
        self.send(header,host,msg)
        for key in self.sessions[session_id]["USERS"].keys():
            if key not in exclude:
                self.send(header,key,msg)

    def add_connection_entry(self,client_id, display_name,session_id,host,conn,addr):
        """
        creates an entry in the connections dictionary for a new connection
        Parameters      : client_id     (str)   -> Represents the client id key to be added to the connections dictionary
                        : display_name  (str)   -> Represents the client's display name
                        : session_id    (str)   -> Represents the session the client belongs to
                        : host          (bool)  -> Represents if the client is the host of the session or not. True => Host, False => User
                        : conn          (socket)-> The client's socket object
                        : addr          (str)   -> Represents The client's ip address and connection port
        """
        self.connections[client_id] = {
            "display_name"  : display_name,
            "session_id"    : session_id,
            "host"          : host,
            "CONN"          : conn,
            "ADDR"          : addr,
            "connected"     : True
        }

    def add_user_to_session(self,session_id,client_id,display_name):
        """
        creates an entry in a session's 'USERS' sub-dictionary for a new user, sets the user's permissions to be empty by default
        Parameters      : session_id    (str)   -> Represents the session id that the client should be added to
                        : client_id     (str)   -> Represents the client id to be added to the session
                        : display_name  (str)   -> Represents the display name of the client
        Returns         : None
        """
        self.sessions[session_id]["USERS"][client_id] = {
            "display_name"  :display_name,
            "permissions"   : {}
        }

    def create_session(self,session_id,host_id,host_name,host_user,host_pass):
        """
        creates a session and fills the host entry
        Parameters      : session_id    (str)   -> Represents the id of the session to be created, sets the users to be empty by default
                        : host_id       (str)   -> Represents the client_id of the host
                        : host_name     (str)   -> Represents the display name of the host
                        : host_user     (str)   -> Represents the host's spotify username
                        : host_pass     (str)   -> Represents the host's spotify password
        Returns         : None
        """
        self.sessions[session_id] = {
            "HOST" : {
                "ID"            : host_id,
                "NAME"          : host_name,
                "spotify_user"  : host_user,
                "spotify_pass"  : host_pass
            },
            "USERS" : {}
        }

    def delete_connection_entry(self,client_id):
        """
        removes a client's dictionary entry
        Parameters      : client_id     (str)   -> Represents the id of the client to be removed
        Returns         : None
        """
        del self.connections[client_id]

    def delete_session_entry(self,session_id,client_id):
        """
        removes a client's dictionary entry from the 'USERS' field of the specifies session id
        Parameters      : session_id    (str)   -> Represents the session the client should be removed from
                        : client_id     (str)   -> Represents the id of the client to be removed
        Returns         : None
        """
        del self.sessions[session_id]["USERS"][client_id]

    def delete_session(self,session_id):
        """
        removes a session from the sessions dictionary
        Parameters      : session_id    (str)   -> Represents the id of the session to be removed
        Returns         : None
        """
        del self.sessions[session_id]

    def get_num_connections(self):
        return threading.activeCount() - 2

    #-----------------------------END HELPER FUNCTIONS-----------------------------#

    def show_connections(self):
        """
        While loop that listens for changes in the threads and print the threads to server console
        Parameters  : None
        Returns     : None
        """
        prev_threads = self.get_num_connections()
        print(f"[Initial Number of Threads] {threading.activeCount()}")
        print(f"[Initial Number of Connections] {self.get_num_connections()}")
        while True:
            if self.get_num_connections() != prev_threads:
                print(f"[CHANGE IN THREADS] Number of Connection threads: {self.get_num_connections()}")
                sleep(0.1)
                self.print_connections()
                self.print_sessions()
                prev_threads = self.get_num_connections()
                for thread in threading.enumerate():
                    print(thread.name)

    def start(self):
        self.server.listen()
        print(f"[STARTING] server is starting\nListening on {SERVER}:{PORT}")
        connections = threading.Thread(target = self.show_connections)
        connections.start()
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target = self.handle_client, args = (conn,addr))
            thread.start()

if __name__ == "__main__":
    server = Server()
    server.start()
