from time import sleep
from random import random
from multiprocessing import Lock
from multiprocessing import Process, Value, Array, Manager
from multiprocessing import Queue
from queue import Empty
import time
import pickle
import socket
import time

#receive data from trains and send acknowldgement back and update train-track table
def receiver(train_table,queue,lock):
    print("receiver started")
    receiver_ip='10.217.59.218'
    receiver_port=2000
    sender_port=3000
   
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind((receiver_ip, receiver_port))

    while True:
        #received data is [gps,trackid,speed,trainid,ack_no]
        data, client_address = receiver_socket.recvfrom(1024)
        data = pickle.loads(data)
        print("data received by server-")
        print(data)
        track_id = data[1] 
        ip_addr, port_no = client_address
        train_id = data[3]
        ack_no = [data[-1]]
        ack_no = pickle.dumps(ack_no)

        #sending acknowledgement
        receiver_socket.sendto(ack_no, (ip_addr,sender_port))
        lock.acquire()
        for tid in train_table:
            if tid != track_id:
                tuple_list = train_table[track_id].copy()
                for tuple in tuple_list:
                    if tuple[0] == train_id:
                        train_table[tid].remove(tuple)
        lock.release()

        tuple = [train_id,ip_addr,port_no]

        lock.aquire()
        if track_id in train_table:
            # Key already exists, append value to the existing list
            if tuple not in train_table[track_id]:
                train_table[track_id].append(tuple)
        else:
            # Key does not exist, create a new entry with a list containing the value
            train_table[track_id] = [tuple]
        lock.release()

        print(f"Updated table: {train_table}")

        queue.put(data[0,4])

#send data to trains in current tracks and wait for acks back
def sender(train_table,queue,lock):
    pending_ack_list=[]
    train_address=0
    queue_empty=0
    
    while True:
        try:
            queue_empty=0
            data=queue.get()
            data = pickle.dumps(data)

        except:
            queue_empty=1

        if queue_empty==0:
            trackid=data[1]
            lock.aquire()
            train_list=train_table[trackid]
            lock.release()

            #tuple = [train_id,ip_addr,port_no]
            for train in train_list:
                train_ip=train[1]
                train_port=3000
                train_address=(train_ip,train_port)
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                server_socket.sendto(data, train_address)

if __name__ == '__main__':
    queue = Queue()
    manager = Manager()
    lock=Lock()
    train_table = manager.dict()
    receiver_process = Process(target=receiver, args=(train_table,queue,lock))
    sender_process = Process(target=sender, args=(train_table,queue,lock))
    sender_process.start()
    receiver_process.start()
    sender_process.join()
    receiver_process.join()
