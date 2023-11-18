import socket
import pickle

class RUDPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.host, self.port))
        self.clients = {}

    def run(self):
        print(f"Server listening on {self.host}:{self.port}")
        while True:
            data, client_address = self.socket.recvfrom(1024)
            message = pickle.loads(data)
            self.process_message(message, client_address)

    def process_message(self, message, client_address):
        if message['type'] == 'connect':
            self.handle_connection(client_address)
        elif message['type'] == 'data':
            self.handle_data(message, client_address)

    def handle_connection(self, client_address):
        client_id = len(self.clients) + 1
        self.clients[client_address] = {'id': client_id}
        print(f"Client {client_id} connected from {client_address}")

    def handle_data(self, message, client_address):
        client_id = self.clients[client_address]['id']
        data = message['data']
        print(f"Received data from Client {client_id}: {data}")

if __name__ == "__main__":
    server = RUDPServer('localhost', 12345)
    server.run()