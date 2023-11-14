import socket
import time

def main():
    server_ip = '10.217.59.110'
    server_port = 12345

    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        # Get user input (message with a number)
        message = input("Enter message with a number to send (type 'exit' to quit): ")

        if message.lower() == 'exit':
            break

        # Send the message to the server
        client_socket.sendto(message.encode(), (server_ip, server_port))

        # Set a timeout for the acknowledgment
        client_socket.settimeout(1.0)

        try:
            # Receive acknowledgment from the server
            ack_data, server_address = client_socket.recvfrom(1024)
            ack_number = int(ack_data.decode().split()[-1])  # Extract the number from the acknowledgment
            print(f"Acknowledgment from server {server_address}: {ack_data.decode()}")

            # Check if the acknowledgment number matches the sent number
            if int(message.split()[-1]) == ack_number:
                print("Acknowledgment received successfully.")
            else:
                print("Received acknowledgment with wrong number. Resending the message.")
                continue
        except socket.timeout:
            # Handle timeout (resend the message)
            print("Timeout! Resending the message.")
            continue

    # Close the socket
    client_socket.close()

if __name__ == "__main__":
    main()
