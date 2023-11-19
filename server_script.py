import socket
import multiprocessing

train_track_dict = dict()
queue = multiprocessing.Queue()

def update_table(queue):
    while True:
        data = queue.get()
        if data.lower() == "close":
            break
        key, value = data.split(" ", 1)

        if key in train_track_dict:
            # Key already exists, append value to the existing list
            if value not in train_track_dict[key]:
                train_track_dict[key].append(value)
        else:
            # Key does not exist, create a new entry with a list containing the value
            train_track_dict[key] = [value]

        print(f"Updated table: {train_track_dict}")

        # Send data to each value in the list associated with the key using UDP
        for val in train_track_dict[key]:
            send_udp_data(val, key)

def send_udp_data(destination, data):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_port = 5000  # You can use any available port
    udp_socket.sendto(data.encode("utf-8"), (destination, udp_port))
    udp_socket.close()

def run_server(queue):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = "127.0.0.1"
    port = 8000
    server.bind((server_ip, port))
    server.listen(0)
    print(f"Listening on {server_ip}:{port}")
    client_socket, client_address = server.accept()
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    while True:
        request = client_socket.recv(1024)
        request = request.decode("utf-8")

        if request.lower() == "close":
            client_socket.send("closed".encode("utf-8"))
            queue.put("close")  # Signal the update_table process to close
            break

        print(f"Received: {request}")

        response = "accepted".encode("utf-8")
        client_socket.send(response)

        # Put the request into the queue for the update_table process
        queue.put(request)

    client_socket.close()
    server.close()

if __name__ == "__main__":
    # Create processes for run_server and update_table
    server_process = multiprocessing.Process(target=run_server, args=(queue,))
    update_process = multiprocessing.Process(target=update_table, args=(queue,))

    # Start both processes
    server_process.start()
    update_process.start()

    # Wait for both processes to finish
    server_process.join()
    update_process.join()
