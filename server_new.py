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

'''
receiver
------------
-runs as a separate process
-receive data from trains
-update the train table based on the received data (delete if present on other track, add if not already present, update ACK no. if on same track)
-put the recived data on queue to be read be sender function (which runs a separate process)
-need to take lock for train_table as it is used by sender function
'''
def receiver(train_table,queue,lock):

    #put our own IP and port on receiver IP and port
    print("receiver started")
    receiver_ip='10.192.241.200'
    receiver_port=2000
    sender_port=3000
    receiver_new_data=0
   
    #start a UDP socket connection for receiver
    receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver_socket.bind((receiver_ip, receiver_port))

    #start receiving data
    while True:
        '''
        #received data is of the format 
        [   gps,    trackid,    speed,  trainid,    ack_no  ]
        '''
        data, client_address = receiver_socket.recvfrom(1024)
        #unpikl the data received
        data = pickle.loads(data)
        print("data received by server-")
        print(data)
        track_id = data[1] 
        ip_addr, port_no = client_address
        train_id = data[3]
        ack_no = [data[-1]]

        #pikl the ACK and send 
        ack_no = pickle.dumps(ack_no)
        receiver_socket.sendto(ack_no, (ip_addr,sender_port))

        #remove the entry if train was present in another track in the table
        lock.acquire()
        for tid in train_table.keys():
            if tid != track_id:
                tuple_list = train_table[tid].copy()
                for tuple in tuple_list:
                    if tuple[0] == train_id:
                        print(tid)
                        print(tuple)
                        train_table[tid].remove(tuple)
        lock.release()

        #Update the train table
        tuple = [train_id,ip_addr,port_no]
        lock.acquire()
        if track_id in train_table.keys():
            # Key already exists, append value to the existing list
            if tuple not in train_table[track_id]:
                train_table[track_id].append(tuple)
        else:
            # Key does not exist, create a new entry with a list containing the value
            train_table[track_id] = [tuple]
        lock.release()

        print(f"Updated table: {train_table}")
        print(data)

        #pikl the data received and put in the queue to be read by sender function
        data_new=pickle.dumps(data[0:4])
        queue.put(data_new)

'''
sender
------------
-runs as a separate process
-read data from queue, do a table lookup and forward the data to respective trains
-need to take lock for train_table as it is used by receiver function
'''
def sender(train_table,queue,lock):
    pending_ack_list=[]
    train_address=0
    queue_empty=0
    
    #read from queue
    while True:
        try:
            queue_empty=0
            data=queue.get(block=False)
            data = pickle.loads(data)

        except:
            queue_empty=1

        if queue_empty==0:
            trackid=data[1]
            print(data)
            lock.acquire()
            train_list=train_table[trackid]
            lock.release()

            #Forward the data to all trains in the tracks
            #tuple = [  train_id,   ip_addr,    port_no]
            for train in train_list:
                train_ip=train[1]
                train_port=3000
                train_address=(train_ip,train_port)
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                packet=pickle.dumps(data)
                server_socket.sendto(packet, train_address)

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
