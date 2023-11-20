from time import sleep
from random import random
from multiprocessing import Lock
from multiprocessing import Process, Value, Array, Manager
from multiprocessing import Queue
from queue import Empty
import time

import socket
import time

#receive data from trains and send acknowldgement back and update train-track table
def receiver(train_table,queue):
    while True:
        data, client_address = server_socket.recvfrom(1024)
        data = pickle.loads(data)
        queue.put(data)
        track_id = data[1] 
        ip_addr, port_no = client_address
        train_id = data[3]
        ack_no = data[-1]

        for key in train_table:
            if key != track_id:
                tuple_list = train_table[key]
                for tuple in tuple_list:
                    if tuple[0] == train_id:
                        train_table.remove(tuple)

        tuple = [train_id,ip_addr,port]
        if train_id in train_table:
            # Key already exists, append value to the existing list
            if tuple not in train_table[key]:
                train_table[key].append(tuple)
        else:
            # Key does not exist, create a new entry with a list containing the value
            train_table[key] = [tuple]

        print(f"Updated table: {train_table}")

        # Send data to each value in the list associated with the key using UDP
        send_udp_data(ip_addr, ack_no)

#send data to trains in current tracks and wait for acks back
def sender(train_table,queue):
    pending_ack_list=[]
    train_address=0
    queue_empty=0
 
    while True:
        try:
            queue_empty=0
            data=queue.get()

        except:
            queue_empty=1

        if queue_empty==0:
            trackid=data[1]
            train_list=train_table[]

    return 0

if __name__ == '__main__':
    queue = Queue()
    manager = Manager()
    train_table = manager.dict()
    sender_process = Process(target=sender, args=(train_table,queue))
    sender_process.start()
    sender_process.join()
