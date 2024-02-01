#!/usr/bin/env python

"""This is the Switch Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
import socket
from datetime import date, datetime

import re
import ast
import threading
import time


# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "switch#.log" # The log file for switches are switch#.log, where # is the id of that switch (i.e. switch0.log, switch1.log). The code for replacing # with a real number has been given to you in the main function.
K = 5
TIMEOUT = 15
# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request Sent

def register_request_sent():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request Sent\n")
    write_to_log(log)

# "Register Response" Format is below:
#
# Timestamp
# Register Response Received

def register_response_received():
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response received\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>.
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>
# ...
# ...
# Routing Complete
# 
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Unresponsive/Dead Neighbor Detected" Format is below:
#
# Timestamp
# Neighbor Dead <Neighbor ID>

def neighbor_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Dead {switch_id}\n")
    write_to_log(log) 

# "Unresponsive/Dead Neighbor comes back online" Format is below:
#
# Timestamp
# Neighbor Alive <Neighbor ID>

def neighbor_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Neighbor Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)
def keep_alive(switch_socket, ID, neighbors, ip_port_list, K):
    # Wait for 5 seconds
    # This is thread 1
    # Send a keep alive message to each of its alive neighbors every 5 seconds
    for neighbor, is_alive in neighbors.items():
        print(f"Neighbor {neighbor} is alive: {is_alive}")
        if is_alive:
            msg = f"{ID} KEEP_ALIVE".encode(encoding='UTF-8')
            switch_socket.sendto(msg, ip_port_list[neighbor])
            print(f"Keep alive sent to neighbor {neighbor}")
def topology_update(switch_socket, neighbors, ip_port_list, server_addr, K):
    # Wait for 5 seconds
    #this is thread 2
    #send a topology update to the controller every 5 seconds
    msg = f"TOPOLOGY_UPDATE {neighbors}".encode(encoding='UTF-8')
    switch_socket.sendto(msg, server_addr)
    print("topology update sent")
def listen_for_neighbors(switch_socket, neighbors, ip_port_list, server_addr, failure_flag_list, TIMEOUT):
    neighbor_addresses = []
    for i in range(len(neighbors)):
        try:
            (data, neighbor_addr) = switch_socket.recvfrom(1024)
            neighbor_addresses.append(neighbor_addr)
            print(f"Server data is '{data.decode('utf-8')}'")
            print(f"Server address is '{neighbor_addr}'")
        except socket.timeout:
            print(f"No message received from neighbor")
            failure_flag_list[0] = True
        except ConnectionResetError:
            print(f"Connection reset by neighbor")
            failure_flag_list[0] = True
            # Handle the connection reset here
            # You can update the failure_flag or take any other necessary actions
        except KeyboardInterrupt:
            print("Keyboard interrupt")
            failure_flag_list[0] = True
def main():

    global LOG_FILE

    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 4:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
        sys.exit(1)
    all_neighbors = {}
    my_id = int(sys.argv[1])
    LOG_FILE = 'switch' + str(my_id) + ".log" 
    # Write your code below or elsewhere in this file
    # first objective is having switches talk with the controller
    # second objective is having switches talk with each other
    # third objective is having switches update their routing tables
    # fourth objective is having switches update their routing tables when a switch goes down
    # fifth objective is having switches update their routing tables when a link goes down
    # sixth objective is having switches update their routing tables when a link comes back up (might not be necessary)
    
    hostname = sys.argv[2] #the hostname directs the socket communication to the controller using the hostname as the IP address
    port = int(sys.argv[3])
    switch_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    address = (hostname, port) # 1b of bootstrap process, Each switch process is provided with its own id, as well as the hostname and port number, that the controller process runs on, as command line arguments. 
    
    #maybe make this into its own function?
    msg = f"REGISTER_REQUEST {my_id}".encode(encoding='UTF-8')
    switch_socket.sendto(msg, address) # 2 of bootstrap process, the switch process sends a register request to the controller process, along with its id. The controller learns the host/port info of the switch from this message
    register_request_sent()
    print(f"The socket is now bound to {switch_socket.getsockname()}")
    print(f"Receiving data from client") #this would be the register response from the controller
    storage = []
    for _ in range(3):
        (data, server_addr) = switch_socket.recvfrom(1024)
        #print(f"Server data is '{data.decode('utf-8')}'")
        storage.append(data.decode('utf-8').split())
    print(storage[0])
    #extract neighbors from storage
    neighbors = []
    if(storage[0][0] == "RESPONSE_NEIGHBORS"):
        #find the numbers in the string and preserve only those in a list of neighbors
        storage[0].pop(0)
        for item in storage[0]:
            neighbors.append(int(re.findall(r'\d+', item)[0]))
    print(len(neighbors))
    #extract alive flag from storage
    alive_flag = 0
    if(storage[1][0] == "RESPONSE_ALIVE_FLAG"):
        alive_flag = int(storage[1][1])
    print(alive_flag)
    #extract neighbor info from storage
    ip_port_list = {}
    if(storage[2][0] == "RESPONSE_NEIGHBOR_INFO"):
        storage[2].pop(0)
        ip_port_list = [(item.strip("'([,])"), int(port.strip("'([])'").replace(',', '').replace(')', ''))) for item, port in zip(storage[2][::2], storage[2][1::2])]
    print(ip_port_list)
    print(type(ip_port_list[0]))
    register_response_received()
    neighbor_ip_port_dict = {}
    for i in range(len(neighbors)):
        neighbor_ip_port_dict[neighbors[i]] = ip_port_list[i]
    print(neighbor_ip_port_dict)
    table = []
    #initial routing table receive
    #there could be more neighbors than the immediate neighbors
    data, server_addr = switch_socket.recvfrom(1024)
    print(f"Server data is '{data.decode('utf-8')}'")
    content = re.findall(r'\d+', data.decode('utf-8'))
    content = [int(num) for num in content]  # Convert numbers to integers
    
    # Group every 3 entries together in a list
    table.append([content[i:i+3] for i in range(0, len(content), 3)])
    table = table[0]
    
    print(neighbor_ip_port_dict)
    routing_table_update(table)
    for neighbor in neighbors:
        all_neighbors[int(neighbor)] = True
    if num_args > 4:
        if sys.argv[4] == "-f":
            neighbor_dead(int(sys.argv[5]))
            all_neighbors[int(sys.argv[5])] = False
    print("This is all neighbors", all_neighbors)

    #1. Each switch sends a Keep Alive message every K seconds to each of the neighboring switches that it thinks is alive
    #2. Each switch sends a Topology Update message every K seconds to the controller. This message contains a list of all the switches that it thinks are alive
    interupt_flag = False
    while not interupt_flag:
        #start thread 1
        time.sleep(K)
        keep_alive_thread = threading.Thread(target=keep_alive, args=(switch_socket, my_id, all_neighbors, neighbor_ip_port_dict, K))
        keep_alive_thread.start()
        #start thread 2
        topology_update_thread = threading.Thread(target=topology_update, args=(switch_socket, all_neighbors, ip_port_list, server_addr, K))
        topology_update_thread.start()
        #start thread 3
        time.sleep(TIMEOUT - K)
        failure_flag_list = [False]
        listen_for_neighbors_thread = threading.Thread(target=listen_for_neighbors, args=(switch_socket, all_neighbors, neighbor_ip_port_dict, server_addr, failure_flag_list, TIMEOUT))
        listen_for_neighbors_thread.start()
        # Wait for the listen_for_neighbors_thread to finish
        listen_for_neighbors_thread.join()
        topology_update_thread.join()
        keep_alive_thread.join()
        print(failure_flag_list)
        # Check if a failure was detected
        if failure_flag_list[0]:
            interupt_flag = True



    #Switch periodic operations:
    #1. Send a keep alive message to each of its neighbors every 5 seconds
    #2. Send a topology update to the controller every 5 seconds. This update a set of alive neighbors
    #3. If a switch hasn't received a keep alive message from a neighbor for 15 seconds, it should mark that neighbor as dead
    #Immediately, it sends a topology update to the controller with an updated list of alive neighbors
    #4. Once a switch receives a keep alive message from a neighbor that it previously marked as dead, it should mark that neighbor as alive, updates host/port info, and sends a topology update to the controller with an updated list of alive neighbors



# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>.
    #routing_table_update
    
if __name__ == "__main__":
    main()