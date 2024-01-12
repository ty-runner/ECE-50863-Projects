#!/usr/bin/env python

"""This is the Switch Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
import socket
from datetime import date, datetime

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "switch#.log" # The log file for switches are switch#.log, where # is the id of that switch (i.e. switch0.log, switch1.log). The code for replacing # with a real number has been given to you in the main function.

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

def main():

    global LOG_FILE

    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 4:
        print ("switch.py <Id_self> <Controller hostname> <Controller Port>\n")
        sys.exit(1)

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
    print(f"Recieving data from client") #this would be the register response from the controller
    (data, server_addr) = switch_socket.recvfrom(1024)
    print(f"Server data is '{data.decode('utf-8')}'")
    
if __name__ == "__main__":
    main()