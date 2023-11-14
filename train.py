import socket

def main():
    server_ip = '10.217.59.110'
    server_port = 12345

    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # Get user input
        message = input("Enter message to send (type 'exit' to quit): ")

        if message.lower() == 'exit':
            break

        # Send the message to the server
        client_socket.sendto(message.encode(), (server_ip, server_port))

        # Receive acknowledgment from the server
        ack_data, server_address = client_socket.recvfrom(1024)
        print(f"Acknowledgment from server {server_address}: {ack_data.decode()}")

    # Close the socket
    client_socket.close()

if __name__ == "__main__":
    main()