import socket

def main():
    server_ip = '10.217.59.110'
    server_port = 12345

    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to a specific address and port
    server_socket.bind((server_ip, server_port))

    print(f"Server listening on {server_ip}:{server_port}")

    while True:
        # Receive data from the client
        data, client_address = server_socket.recvfrom(1024)
        print(f"Received data from {client_address}: {data.decode()}")

        # Acknowledge the receipt of the message
        ack_message = "ACK: Message received"
        server_socket.sendto(ack_message.encode(), client_address)

if __name__ == "__main__":
    main()