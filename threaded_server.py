import socket
import threading
import json

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

    def handle_client(self,conn,addr):
        print(f"[NEW CONNECTION] {addr} connected")

        connected = True
        while connected:
            msg_length = conn.recv(PREFIX).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                raw_msg = conn.recv(msg_length).decode(FORMAT)
                message = json.loads(raw_msg)

                if message["MESSAGE"] == DISCONNECT_MESSAGE:
                    connected = False

                elif message["HEADER"] == "CTC":
                    dest = message["DEST"]
                    self.send("CTC", dest, message["ID"], message["MESSAGE"])

                elif message["HEADER"] == "INIT":
                    identifier = json.loads(message["MESSAGE"])
                    self.connections[identifier["ID"]] = {"NAME" : identifier["NAME"], "CONN": conn}
                    print(self.connections.keys())

                else:
                    print(f"[{addr}, {self.connections[message['ID']]['NAME']}] {message['MESSAGE']}")

        del self.connections[message["ID"]]
        print(self.connections.keys())
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
