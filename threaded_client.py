import socket
import json
import uuid
import threading

PREFIX = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)

HEADERS = ["CTS", "CTC", "INIT"]

class Client:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.client.connect(ADDR)
        self.init_connection()
        self.reciever = threading.Thread(target=self.recv_msg)
        self.reciever.start()


    def init_connection(self):
        identifier = {"NAME":self.name, "ID": self.id}
        self.send("INIT", "Server", json.dumps(identifier))

    def recv_msg(self):
        while True:
            msg = self.client.recv(2048)
            print(msg)

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

    def create_disconnect_message(self):
        return self.create_message("CTS", "Server", DISCONNECT_MESSAGE)

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
    x = input("enter your name")
    client = Client(x, str(uuid.uuid4()))
    client.send("CTS", "Server", "Hello World")
    while True:
        header = input("What kind of header")
        dest = input("who do you want to send to")
        msg = input("What message do you want to send")
        client.send(header, dest, msg)
        if msg == DISCONNECT_MESSAGE:
            break
