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
    
    return 0

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
            
    return 0

if __name__ == '__main__':
    queue = Queue()
    manager = Manager()
    train_table = manager.dict()
    sender_process = Process(target=sender, args=(train_table,queue))
    sender_process.start()
    sender_process.join()
