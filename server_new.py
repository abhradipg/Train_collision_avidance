from time import sleep
from random import random
from multiprocessing import Process
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
    return 0