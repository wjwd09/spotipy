import socket
import threading
import json
import random, string
from time import sleep
from spotifyServer import *
import queue
import pickle

PREFIX = 64
PORT = 25564
SERVER = ''
#SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
HEADERS = ["STC", "CURRENT_SONG","BROADCAST","SESSION_ID","SESSION_INFO", "BROADCAST_S","FAILURE", DISCONNECT_MESSAGE,"USER_DISCONNECT","USER_JOINED","USER_DISCONNECT_UNEXPECTED", "SET_PERMISSIONS", "GET_CURRENT_SONG", "REWIND", "PLAY", "SKIP","USERS","SEARCH_RESULTS","PERMISSION_UPDATE","QUEUE_UPDATE"]
FAILURE_MESSAGE = {"HEADER": "MESSAGE_FAILURE", "MESSAGE": "FAILURE"}
class Server:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind(ADDR)
        self.connections = {} #dictionary of all connections
        self.sessions = {} #dictionary of all sessions. Consists of a host & a sub dictionary of users



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
                try:
                    msg_length = conn.recv(PREFIX).decode(FORMAT)
                except:
                    print(f"[{addr}] DISCONNECTED")
                    self.handle_unexpected_disconnect(client_id,conn)
                    return

                if msg_length:
                    try:
                        msg_length = int(msg_length)
                        try:
                            raw_msg = conn.recv(msg_length).decode(FORMAT)
                        except:
                            print(f"[{addr}] DISCONNECTED")
                            self.handle_unexpected_disconnect(client_id,conn)
                            return
                        message = json.loads(raw_msg)
                    except ValueError:
                        message = FAILURE_MESSAGE

                    if message["HEADER"] == DISCONNECT_MESSAGE:
                        connected = False
                        self.handle_disconnect(message,conn)

                    elif message["HEADER"] == "CREATE":
                        session_id = "".join(random.choices(string.ascii_uppercase + string.digits, k = 4))
                        indentifer = json.loads(message["MESSAGE"])
                        tokenDict = json.loads(indentifer["spotify_token"])
                        client_id = message["ID"]
                        self.create_session(session_id, message["ID"], indentifer["display_name"], tokenDict)
                        self.add_connection_entry(message["ID"], indentifer["display_name"], session_id, True, conn, addr)
                        self.create_spotify_player(session_id)
                        if not self.sessions[session_id]["HOST"]["spotify_player"].is_spotify_running():
                            self.send("STC", client_id, "PLEASE START SPOTIFY")

                        self.send("SESSION_ID", client_id,  str(session_id))

                    elif message["HEADER"] == "GET_CURRENT_SONG":
                        player = self.get_session_player(self.get_session_from_user(message["ID"]))
                        if not self.sessions[session_id]["HOST"]["spotify_player"].is_spotify_running():
                            self.send("STC", client_id, "PLEASE START SPOTIFY")
                        else:
                            current_track = {}
                            current_track["name"] = player.sp.currently_playing()['item']['name']
                            current_track["artist"] = player.sp.currently_playing()['item']['album']['artists'][0]['name']
                            track_json = json.dumps(current_track)
                            self.send("CURRENT_SONG", message["ID"],track_json)

                    elif message["HEADER"] == "SKIP":
                        player = self.get_session_player(self.get_session_from_user(message["ID"]))
                        session_id = self.get_session_from_user(message["ID"])
                        session_queue =  self.get_session_queue(session_id)
                        if len(session_queue) > 0:
                            player.add_to_queue(session_queue[0][1])
                            session_queue.pop(0)
                            self.send_queue_update(session_id)
                        player.next_track()

                    elif message["HEADER"] == "REWIND":
                        player = self.get_session_player(self.get_session_from_user(message["ID"]))
                        player.previous_track()

                    elif message["HEADER"] == "PLAY":
                        session_id = self.get_session_from_user(message["ID"])
                        player = self.get_session_player(self.get_session_from_user(message["ID"]))
                        player.toggle_playback()

                    elif message["HEADER"] == "SEARCH":
                        player = self.get_session_player(self.get_session_from_user(message["ID"]))
                        song = message["MESSAGE"]
                        self.send("SEARCH_RESULTS", message["ID"], json.dumps(player.search(song)))




                    elif message["HEADER"] == "ADD_TO_QUEUE":
                        track_data = json.loads(message["MESSAGE"])
                        self.add_to_session_queue(message["ID"], (track_data["name"],track_data['uri']))
                        session_id = self.get_session_from_user(message["ID"])


                    elif message["HEADER"] == "QUEUE_UPDATE":
                        options = json.loads(message["MESSAGE"])
                        self.update_queue(message["ID"],options)

                    elif message["HEADER"] == "GET_USERS":
                        session_id = self.get_session_from_user(message["ID"])
                        users = self.sessions[session_id]["USERS"]
                        self.send("USERS", message["ID"], json.dumps(users))

                    elif message["HEADER"] == "SET_PERMISSION":
                        msg = json.loads(message["MESSAGE"])
                        session_id = self.get_session_from_user(message["ID"])
                        self.change_user_permissions(session_id, msg["client_id"], msg["permission"])
                        new_permissions = {}
                        new_permissions["permission"] = msg["permission"]
                        new_permissions["value"] = self.sessions[session_id]["USERS"][msg["client_id"]]["permissions"][msg["permission"]]
                        self.send("PERMISSION_UPDATE",msg["client_id"], json.dumps(new_permissions))

                    elif message["HEADER"] == "JOIN":
                        msg = json.loads(message["MESSAGE"])
                        session_id = msg["session_id"]
                        if session_id in self.sessions.keys():
                            self.add_user_to_session(session_id,message["ID"],msg["display_name"])
                            self.add_connection_entry(message["ID"],msg["display_name"],session_id, False, conn, addr)
                            client_id = message["ID"]

                            session_info = {}
                            session_info["session_id"] = session_id
                            session_info["host"] = self.sessions[session_id]["HOST"]["NAME"]

                            self.send("SESSION_INFO", message["ID"], json.dumps(session_info))
                            self.send("QUEUE_UPDATE", message["ID"], json.dumps(self.get_session_queue(session_id)))
                            self.broadcast_to_session(session_id,"USERS", json.dumps(self.sessions[session_id]["USERS"]))
                        else:
                            self.add_connection_entry(message["ID"],msg["display_name"],session_id, False, conn, addr)
                            self.send("FAILURE", message["ID"], "Session does not exist")
                            self.send(DISCONNECT_MESSAGE,message["ID"],DISCONNECT_MESSAGE)
                            self.delete_connection_entry(message["ID"])
                            break
                    elif message["HEADER"] == "SET_PERMISSIONS":
                        msg = json.loads(message["MESSAGE"])
                        user_id = msg["client_id"]
                        permissions = json.loads(msg["permissions"])
                        for key in permissions.keys():
                            self.set_permissions(user_id,key,permissions[key])
                        self.print_sessions()

                    elif message["HEADER"] == "BROADCAST_S":
                        session_id = self.connections[message["ID"]]["session_id"]
                        self.broadcast_to_session(session_id,"BROADCAST_S", message["MESSAGE"])
                    elif message["HEADER"] == "BROADCAST":
                        self.broadcast_to_all("BROADCAST", message["MESSAGE"])

                    elif message["HEADER"] == "PLAYBACK":
                        session_id = self.connections[message["ID"]]["session_id"]
                        sp = self.sessions[session_id]["HOST"]["spotify_player"]
                        if not sp.toggle_playback():
                            self.broadcast_to_session(self.get_session_from_user(client_id), "FAILURE", "Please Start Spotify")

                    else:
                        print(message["MESSAGE"])
            except Exception as ex:
                print(str(ex))

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
            host = message["ID"]
            session_location = self.connections[message["ID"]]["session_id"]
            for key in self.sessions[session_location]["USERS"].keys():
                self.disconnect(self.connections[key]["CONN"],message["ID"],f"[HOST <{host}>:<{self.connections[host]['display_name']}>] Unexpectedly Disconnected") #close each connection
                self.delete_connection_entry(key) #delete the connection from the connections dictionary
            self.delete_session(session_location) # delete the session
            self.delete_connection_entry(message["ID"])
            self.disconnect(conn,message["ID"], "You Disconnected")
        else:
            session_location = self.connections[message["ID"]]["session_id"]
            self.delete_session_entry(session_location,message["ID"])
            self.broadcast_to_session(session_location, "USER_DISCONNECT",f"[USER <{message['ID']}>:<{self.connections[message['ID']]['display_name']}>] Disconnected", exclude=[message["ID"]])
            self.delete_connection_entry(message["ID"])
            self.broadcast_to_session(session_location, "USERS", json.dumps(self.sessions[session_location]["USERS"]))
            self.disconnect(conn,message["ID"],"You Disconnected")

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
                    self.disconnect(self.connections[key]["CONN"],client_id,f"[HOST <{client_id}>:<{self.connections[client_id]['display_name']}>] Unexpectedly Disconnected") #close each connection
                    self.delete_connection_entry(key) #delete the connection from the connections dictionary
                self.delete_session(session_location) # delete the session
                self.delete_connection_entry(client_id) # delete the original client entry from connections
                self.disconnect(conn,client_id,"You Disconnected")
            else:
                session_location = self.connections[client_id]["session_id"]
                self.delete_session_entry(session_location,client_id)
                self.broadcast_to_session(session_location, "USER_DISCONNECT_UNEXPECTED",f"[USER <{client_id}>:<{self.connections[client_id]['display_name']}>] Unexpectedly Disconnected", exclude=[client_id])
                self.delete_connection_entry(client_id)
                self.disconnect(conn,client_id,"You Disconnected")
        except:
            print("Something went wrong")




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
            sleep(0.1)
            conn.send(message)

    def set_permissions(self, user, permission, value):
        session = self.get_session_from_user(user)
        if permission in self.sessions[session]["USERS"][user]["permissions"].keys():
            self.sessions[session]["USERS"][user]["permissions"][permission] = value
            return True
        else:
            return False
    #-----------------------------HELPER FUNCTIONS-----------------------------#
    def create_disconnect_message(self,dest, reason):
        return self.create_message(DISCONNECT_MESSAGE, dest, reason)

    def disconnect(self,conn,dest,reason):
        """
        Sends a disconnect message to a specified conn object then closes the connection
        Parameters      : conn      (socket)    ->  The connection to be disconnected
        Returns         : None
        """
        discon_msg = self.create_disconnect_message(dest,reason)
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
            "permissions"   : {
                "add_to_queue"      : True,
                "playback"          : True,
                "skip"              : True,
                "edit_queue"        : True
            }
        }

    def change_user_permissions(self, session_id, client_id, permission):
        permission_value = self.sessions[session_id]["USERS"][client_id]["permissions"][permission]
        if permission_value == True:
            self.sessions[session_id]["USERS"][client_id]["permissions"][permission] = False
        elif permission_value == False:
            self.sessions[session_id]["USERS"][client_id]["permissions"][permission] = True

    def create_session(self,session_id,host_id,host_name,spotify_token):
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
                "spotify_token" : spotify_token,
                "spotify_player": None,
            },
            "queue"             : [],
            "queue_lock"        : False,
            "current_track"     : "",
            "previous_track"    : "",
            "USERS"             : {}
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

    def create_spotify_player(self, session_id):
        token = self.sessions[session_id]["HOST"]["spotify_token"]
        self.sessions[session_id]["HOST"]["spotify_player"] = spotifyServer(accToken=None, accTokenDict=token)

    def get_session_queue(self, session_id):
        return self.sessions[session_id]["queue"]

    def get_session_player(self, session_id):
        return self.sessions[session_id]["HOST"]["spotify_player"]

    def add_to_session_queue(self, user_id, data):
        session = self.get_session_from_user(user_id)
        self.sessions[session]["queue"].append(data)
        self.send_queue_update(session)

    def update_queue(self, user_id, options):
        session_id = self.get_session_from_user(user_id)
        session_queue = self.get_session_queue(session_id)
        if options["action"] == "DELETE":
            print("Deleting song", options["song_index"])
            session_queue.pop(options["song_index"])
        elif options["action"] == "MOVE_UP":
            if len(session_queue) >= 2 and options["song_index"] > 0:
                temp = session_queue[options["song_index"]-1]
                session_queue[options["song_index"] -1] = session_queue[options["song_index"]]
                session_queue[options["song_index"]] = temp
        elif options["action"] == "MOVE_DOWN":
            if len(session_queue) >= 2 and options["song_index"] < len(session_queue)-1:
                temp = session_queue[options["song_index"]+1]
                session_queue[options["song_index"] +1] = session_queue[options["song_index"]]
                session_queue[options["song_index"]] = temp

        self.send_queue_update(session_id)

    def send_queue_update(self,session_id):
        self.broadcast_to_session(session_id,"QUEUE_UPDATE", json.dumps(self.get_session_queue(session_id)))

    def check_song_progress(self):
        counter = 0
        while(1):
            sleep(1)
            try:
                for session in self.sessions.keys():
                    try:
                        if self.get_session_player(session).is_spotify_running() != False:
                            player = self.get_session_player(session)
                            progress_percentage = round(player.get_song_progress_ms()/self.get_session_player(session).get_song_duration_ms(), 2)
                            current_track = {}
                            current_track["name"] = player.sp.currently_playing()['item']['name']
                            current_track["artist"] = player.sp.currently_playing()['item']['album']['artists'][0]['name']
                            current_track["progress"] = player.get_song_progress_ms()
                            current_track["runtime"] = player.get_song_duration_ms()

                            self.sessions[session]["current_track"] = player.sp.currently_playing()['item']['uri']


                            track_json = json.dumps(current_track)
                            if len(track_json) >= 1:
                                self.broadcast_to_session(session, "CURRENT_SONG", track_json)
                            else:
                                self.broadcast_to_session(session, "STC", "PLEASE START SPOTIFY")

                            if counter % 2 == 0:
                                self.send_queue_update(session)

                            if progress_percentage > 0.98 and counter % 4:
                                if len(self.get_session_queue(session)) > 0  and not self.sessions[session]["queue_lock"]:
                                    print(f"adding song: {current_track['name']} to shared queue for session {session}")
                                    try:
                                        self.get_session_player(session).add_to_queue(self.get_session_queue(session)[0][1])
                                        self.get_session_queue(session).pop(0)
                                        self.sessions[session]["previous_track"] = self.sessions[session]["current_track"]
                                        self.send_queue_update(session)
                                        self.sessions[session]["queue_lock"] = True
                                    except Exception as ex:
                                        print(str(ex))
                            else:
                                if self.sessions[session]["previous_track"] != self.sessions[session]["current_track"] and self.sessions[session]["queue_lock"]:
                                    self.sessions[session]["queue_lock"] = False
                    except:
                        pass
            except:
                pass
            counter+=1
            if counter == 1000:
                counter = 0

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
        #connections = threading.Thread(target = self.show_connections)
        #connections.start()

        prog = threading.Thread(target = self.check_song_progress)
        prog.start()



        while True:
            conn, addr = self.server.accept()
            conn.setblocking(1)
            thread = threading.Thread(target = self.handle_client, args = (conn,addr))
            thread.start()




if __name__ == "__main__":
    server = Server()
    server.start()
    server.server.close()
