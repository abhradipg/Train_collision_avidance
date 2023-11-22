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
                break
            elif slowdown.value == 1:
                sleep(20)
            else:
                sleep(6)
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
                    #print("put data", data)
                else:
                    # Handle the case where data is not in my_dict
                    print(f"Data {data} not found in my_dict")


def sender(queue,shared_gps,curr_ack,received_ack,ack_lock,lock):
    server_ip = '10.114.241.211'
    server_port = 2000
    server_addr = (server_ip, server_port)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    
    queue_empty=0
    data=[]
    
    ack_lock.acquire()
    received_ack.value=1
    curr_ack.value=0
    ack_lock.release()
    rtt_approx=4
    speed=100
    train_id=12340
    curr_time=0
    send_time=0
    ack_no=0

    while True:
        sleep(0.1)
        try:
            queue_empty=0
            data = queue.get(block=False)
            print("read new rfid")
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
            #print("sending rfid data")
            #print(data)
            data = pickle.dumps(data)
            client_socket.sendto(data, (server_ip, server_port))
        
        if received_ack.value==0:
            curr_time=time.time()
            if curr_time - send_time > rtt_approx:
                send_time = time.time()
                print("Ack not received resending data")
                #print(data)
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
    #print("distance is - "+str(distance))
    return distance

def print_metrics(segments,distance,speed_lock):
    train_id=segments[3]
    speed=segments[2]
    source_ip=segments[4]
    source_port=2500
    server_address = (source_ip,source_port)

    print("Train ID: ",str(train_id)," is at location: ",str(segments[0][0]),"\u00B0 N ",str(segments[0][1]),"\u00B0 E")
    print("Speed of train is: ",str(speed),"km/hr \n")
    print("Distance between trains is: ",str(distance),"km \n")
    if distance < 0.300:
        speed_lock.acquire()
        slowdown.value = 2
        speed_lock.release()
        print("Braking !!! Dangerously Close")
        print(server_address)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        try:
            client_socket.connect(server_address)
            message="stop"
            client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print('Error handling client connection:', e)
        finally:
            client_socket.close()

    elif distance < 1:
        speed_lock.acquire()
        if slowdown.value != 2: 
            slowdown.value = 1
        speed_lock.release()
        if slowdown.value != 2:
            print("Slowing down !!!")
            print(server_address)
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,1)
        try:
            client_socket.connect(server_address)
            message="slow"
            client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print('Error handling client connection:', e)
        finally:
            client_socket.close()
    


def receiver(shared_gps,curr_ack,slowdown,received_ack,ack_lock,lock,speed_lock):
    server_ip = '10.114.241.208'
    #server_ip = '10.192.240.106'
    server_port = 3000
    forward_train_gps = 0
    train_id=12340
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((server_ip, server_port))
    print("binded")
    while True:
        #sleep(0.2)
        #print("in while")
        data, client_address = server_socket.recvfrom(1024)
        #print("received data")
        segments = pickle.loads(data)
        print(segments)
        if len(segments)==1:
            ack_no=segments[0]
            #print("got ack")
            print(ack_no)
            ack_lock.acquire()
            print(curr_ack.value)
            if ack_no==curr_ack.value:
                received_ack.value=1
            ack_lock.release()
        else:
            #segment data format [[gps],trackid,speed,train_no,sourceip,ackno]
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
            lock.acquire()
            curr_gps=[shared_gps[0],shared_gps[1]]
            lock.release()
            distance=process_data(curr_gps[0],curr_gps[1],forward_train_gps[0],forward_train_gps[1])

            print_metrics(segments,distance,speed_lock)

def tcp_server(slowdown,speed_lock):
    server_ip='10.114.241.208'
    server_port=2500
    server_address = (server_ip,server_port)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind(server_address)
    server_socket.listen(10)

    while True:
        # Wait for a connection
        #print('Waiting for a connection...')
        client_socket, client_address = server_socket.accept()
        #print('Accepted connection from {}:{}'.format(*client_address))

        # Receive and print the data
        data = client_socket.recv(1024)
        if data:
            message = data.decode('utf-8')
            print(message)
            if(message=="slow"):
                speed_lock.acquire()
                if slowdown.value != 2: 
                    slowdown.value = 1
                speed_lock.release()
                if slowdown.value != 2:
                    print("Train Slowing down !!!")

            elif(message=="stop"):
                speed_lock.acquire()
                slowdown.value = 2
                speed_lock.release()
                print("Braking !!! Train Dangerously Close")

        # Close the connection
        client_socket.close()

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
    tcp_process = Process(target=tcp_server, args=(slowdown,speed_lock))
    tcp_process.start()
    reader_process = Process(target=rfid_reader, args=(queue,slowdown,speed_lock))
    reader_process.start()
    sender_process = Process(target=sender, args=(queue,shared_gps,curr_ack,received_ack,ack_lock,lock))
    sender_process.start()
    reciver_process = Process(target=receiver, args=(shared_gps,curr_ack,slowdown,received_ack,ack_lock,lock,speed_lock))
    reciver_process.start()
    reader_process.join()
    sender_process.join()
    reciver_process.join()
    tcp_process.join()

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