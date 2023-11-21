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

def rfid_reader(queue,slowdown,speed_lock):
    my_dict=generate_dict.generate_dict()
    old_data=''
    file_path = 'dummy_data2.txt'
    #while True:
    with open(file_path, 'r') as file:
        for line in file:
            speed_lock.acquire()
            if(slowdown.value == 2):
                sleep(3000)
            elif slowdown.value == 1:
                sleep(15)
            else:
                sleep(5)
            speed_lock.release()

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
    server_ip = '10.192.241.200'
    server_port = 2000
    server_addr = (server_ip, server_port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    
    queue_empty=0
    data=[]
    
    ack_lock.acquire()
    received_ack.value=1
    curr_ack.value=0
    ack_lock.release()
    rtt_approx=5
    speed=100
    train_id=12340
    curr_time=0
    send_time=0
    ack_no=0

    while True:
        sleep(0.2)
        try:
            queue_empty=0
            data = queue.get(block=False)
            print("received new data")
            lock.acquire()
            shared_gps[0]=data[0][0]
            shared_gps[1]=data[0][1]
            lock.release()
        except Empty:
            queue_empty = 1

        if queue_empty == 0:
            data.append(speed)
            data.append(train_id)
            data.append(ack_no)
            ack_lock.acquire()
            curr_ack.value=ack_no
            ack_no=ack_no+1
            received_ack.value=0
            ack_lock.release()
            send_time=time.time()
            print("sending data")
            print(data)
            data = pickle.dumps(data)
            client_socket.sendto(data, (server_ip, server_port))
        
        if received_ack.value==0:
            curr_time=time.time()
            if curr_time - send_time > rtt_approx:
                send_time = time.time()
                print("resending data")
                print(data)
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
    print("distance is - "+str(distance))
    return distance

def print_metrics(segments,distance):
    train_id=segments[3]
    speed=segments[2]
    print("Train ID: ",str(train_id)," is at location: ",str(segments[0][0]),"\u00B0 N ",str(segments[0][1]),"\u00B0 E")
    print("Speed of train is: ",str(speed),"km/hr \n")
    print("Distance between trains is: ",str(distance),"km \n")
    if distance < 0.300:
        speed_lock.acquire()
        slowdown.value = 2
        speed_lock.release()
        print("Braking !!! Dangerously Close")
    elif distance < 1:
        speed_lock.acquire()
        slowdown.value = 1
        speed_lock.release()
        print("Slowing down !!!")
    


def receiver(shared_gps,curr_ack,slowdown,received_ack,ack_lock,lock,speed_lock):
    #server_ip = '10.192.241.2'
    server_ip = '10.192.240.184'
    server_port = 3000
    forward_train_gps = 0
    train_id=12340
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))
    print("binded")
    while True:
        #sleep(0.2)
        print("in while")
        data, client_address = server_socket.recvfrom(1024)
        print("received data")
        segments = pickle.loads(data)
        print(segments)
        if len(segments)==1:
            ack_no=segments[0]
            print("got ack")
            print(ack_no)
            ack_lock.acquire()
            print(curr_ack)
            if ack_no==curr_ack.value:
                received_ack.value=1
            ack_lock.release()
        else:
            ack_message = [segments[-1]]
            ack_message.append(train_id)
            print("train ack")
            print(segments[-1])
            print(ack_message)
            ack_message = pickle.dumps(ack_message)
            client_ip, client_port = client_address
            client_port = 2000
            server_socket.sendto(ack_message, (client_ip,client_port))
            forward_train_gps=segments[0]
            distance=process_data(shared_gps[0],shared_gps[1],forward_train_gps[0],forward_train_gps[1])
            print_metrics(segments,distance)

if __name__ == '__main__':
    queue = Queue()
    shared_gps = Array('d', [0.0, 0.0])
    curr_ack = Value('i') 
    slowdown = Value('i')
    slowdown.value = 0
    received_ack = Value('i') 
    lock=Lock()
    ack_lock=Lock()
    speed_lock=Lock()
    reader_process = Process(target=rfid_reader, args=(queue,slowdown,speed_lock))
    reader_process.start()
    sender_process = Process(target=sender, args=(queue,shared_gps,curr_ack,received_ack,ack_lock,lock))
    sender_process.start()
    reciver_process = Process(target=receiver, args=(shared_gps,curr_ack,slowdown,received_ack,ack_lock,lock,speed_lock))
    reciver_process.start()
    reader_process.join()
    sender_process.join()
    reciver_process.join()

'''
class RTOCalculator:
    def __init__(self, initial_rtt):
        self.ertt = initial_rtt
        self.drtt = 0

    def update_rtt(self, measured_rtt):
        # Update ERTT and DRTT based on the measured RTT
        alpha = 0.125  # Weighting factor for ERTT
        beta = 0.25   # Weighting factor for DRTT

        self.ertt = (1 - alpha) * self.ertt + alpha * measured_rtt
        self.drtt = (1 - beta) * self.drtt + beta * abs(measured_rtt - self.ertt)

    def calculate_rto(self):
        # Calculate RTO using the ERTT and DRTT formula
        return self.ertt + 4 * self.drtt

# Example usage
initial_rtt = 0.1  # Initial Round-Trip Time (seconds)
rto_calculator = RTOCalculator(initial_rtt)

# Simulate updating RTT measurements
measured_rtt_values = [0.12, 0.15, 0.11, 0.13]
for measured_rtt in measured_rtt_values:
    rto_calculator.update_rtt(measured_rtt)
    calculated_rto = rto_calculator.calculate_rto()
    print(f"Measured RTT: {measured_rtt}, Calculated RTO: {calculated_rto}")

'''