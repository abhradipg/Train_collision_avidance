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
    while True:
        data = reader()
        sleep(2)
        queue.put(data)
        print("put data",data)

def sender(queue):
    server_ip = '10.217.59.110'
    server_port = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    queue_empty=0
    data=0
    old_data=0
    received_ack=0
    ack_no=0
    curr_ack
    rtt_approx=1

    while True:
        try:
            queue_empty=0
            data = queue.get(block=False)
        except Empty:
            queue_empty = 1

        if old_data==data:
            queue_empty=1

        if queue_empty==0:
            old_data=data

        if queue_empty == 0:
            data = data+","+time.time()+","+ack_no
            curr_ack=ack_no
            ack_no=ack_no+1
        
        curr_time=time.time()
        client_socket.sendto(data.encode(), (server_ip, server_port))
        

        
        

def reciver():
    return 0

