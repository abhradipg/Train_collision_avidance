from time import sleep
from random import random
from multiprocessing import Process
from multiprocessing import Queue
from queue import Empty
import time

import socket
import time

def reader():
    return random()

def rfid_reader(queue):
    old_data=0
    while True:
        data = reader()
        if data!=old_data:
            old_data=data
            sleep(2)
            queue.put(data)
            print("put data",data)

def sender(queue):
    server_ip = '10.217.59.110'
    server_port = 2000
    server_addr = (server_ip, server_port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    queue_empty=0
    data=0
    old_data=0
    received_ack=0
    ack_no=0
    curr_ack
    rtt_approx=1
    speed=100

    while True:
        try:
            queue_empty=0
            data = queue.get(block=False)
        except Empty:
            queue_empty = 1

        if queue_empty == 0:
            data = data+","+speed+","+ack_no
            curr_ack=ack_no
            ack_no=ack_no+1
            received_ack=0
            #curr_time=time.time()
            client_socket.sendto(data.encode(), (server_ip, server_port))
        
        if received_ack==0:
            client_socket.settimeout(rtt_approx)
            try:
                ack_data, server_address = client_socket.recvfrom(1024)
                if server_address==server_addr and ack_data==ack_no:
                    received_ack=1

            except socket.timeout:
                received_ack=0

def reciver():
    server_ip = '10.217.59.110'
    server_port = 3000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind((server_ip, server_port))

    while True:
        data, client_address = server_socket.recvfrom(1024)
        segments = data.split(',')
        ack_message = segments[-1]
        server_socket.sendto(ack_message.encode(), client_address)
        process_data(segments[:-2])

def process_data():
    return 0

if __name__ == '__main__':
    queue = Queue()
    reader_process = Process(target=rfid_reader, args=(queue,))
    reader_process.start()
    sender_process = Process(target=sender, args=(queue,))
    sender_process.start()
    reciver_process = Process(target=reciver)
    reader_process.join()
    sender_process.join()
    reciver_process.join()
