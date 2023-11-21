from time import sleep
from random import random
from multiprocessing import Lock
from multiprocessing import Process, Value, Array
from multiprocessing import Queue
from queue import Empty
import time
from math import radians, sin, cos, sqrt, atan2
import socket
import time
import ast
import pickle
import generate_dict

my_dict = {}

def rfid_reader(queue):
    my_dict=generate_dict.generate_dict()
    old_data=''
    file_path = 'dummy_data1.txt'
    #while True:
    with open(file_path, 'r') as file:
        for line in file:
            sleep(1)
            if "'EPCData':" in line:
                # Convert the string representation of the dictionary to an actual dictionary
                data_dict = ast.literal_eval(line.strip())
                # Extracting the 'EPC' value and return it
                data=data_dict['EPCData']['EPC']

            if data!=old_data:
                old_data=data
                if data in my_dict:
                    queue.put(my_dict[data])
                    print("put data", data)
                else:
                    # Handle the case where data is not in my_dict
                    print(f"Data {data} not found in my_dict")


def sender(queue,shared_gps,curr_ack,received_ack,ack_lock,lock):
    server_ip = '10.217.59.218'
    server_port = 2000
    server_addr = (server_ip, server_port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    
    queue_empty=0
    data=[]
    
    ack_lock.acquire()
    received_ack=1
    curr_ack=0
    ack_lock.release()
    rtt_approx=1
    speed=100
    train_id=12345
    curr_time=0
    send_time=0
    ack_no=0

    while True:
        try:
            queue_empty=0
            data = queue.get(block=False)
            print("received new data")
            lock.acquire()
            shared_gps=data[0]
            lock.release()
        except Empty:
            queue_empty = 1

        if queue_empty == 0:
            data.append(speed)
            data.append(train_id)
            data.append(ack_no)
            curr_ack=ack_no
            ack_lock.acquire()
            ack_no=ack_no+1
            received_ack=0
            ack_lock.release()
            send_time=time.time()
            data = pickle.dumps(data)
            client_socket.sendto(data, (server_ip, server_port))
        
        if received_ack==0:
            curr_time=time.time()
            if curr_time - send_time > rtt_approx:
                send_time = time.time()
                client_socket.sendto(data, (server_ip, server_port))

def process_data(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Radius of the Earth in kilometers (change it to 3958.8 for miles)
    radius = 6371.0

    # Calculate the distance
    distance = radius * c
    print("distance is - "+distance)
    return distance

def receiver(shared_gps,curr_ack,received_ack,ack_lock,lock):
    server_ip = '127.0.0.1'
    server_port = 3000
    forward_train_gps = 0

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind((server_ip, server_port))

    while True:
        data, client_address = server_socket.recvfrom(1024)
        segments = pickle.loads(data)
        if len(segments)==1:
            ack_no=segments[0]
            print("got ack")
            print(ack_no)
            ack_lock.acuire()
            if ack_no==curr_ack:
                received_ack=1
            ack_lock.release()
        else:
            ack_message = segments[-1]
            client_ip, client_port = client_address
            client_port = 2000
            server_socket.sendto(ack_message.encode(), (client_ip,client_port))
            forward_train_gps=segments[0]
            process_data(shared_gps[0],shared_gps[1],forward_train_gps[0],forward_train_gps[1])

if __name__ == '__main__':
    queue = Queue()
    shared_gps = Array('d', [0.0, 0.0])
    curr_ack = Value('i') 
    received_ack = Value('i') 
    lock=Lock()
    ack_lock=Lock()
    reader_process = Process(target=rfid_reader, args=(queue,))
    reader_process.start()
    sender_process = Process(target=sender, args=(queue,shared_gps,curr_ack,received_ack,ack_lock,lock))
    sender_process.start()
    reciver_process = Process(target=receiver, args=(shared_gps,curr_ack,received_ack,ack_lock,lock))
    reciver_process.start()
    reader_process.join()
    sender_process.join()
    reciver_process.join()
