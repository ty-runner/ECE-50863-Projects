#!/usr/bin/env python

"""This is the Controller Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
import socket
from datetime import date, datetime

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "Controller.log"

# Those are logging functions to help you follow the correct logging standard

# "Register Request" Format is below:
#
# Timestamp
# Register Request <Switch-ID>

def register_request_received(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Request {switch_id}\n")
    write_to_log(log)

# "Register Responses" Format is below (for every switch):
#
# Timestamp
# Register Response <Switch-ID>

def register_response_sent(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Register Response {switch_id}\n")
    write_to_log(log) 

# For the parameter "routing_table", it should be a list of lists in the form of [[...], [...], ...]. 
# Within each list in the outermost list, the first element is <Switch ID>. The second is <Dest ID>, and the third is <Next Hop>, and the fourth is <Shortest distance>
# "Routing Update" Format is below:
#
# Timestamp
# Routing Update 
# <Switch ID>,<Dest ID>:<Next Hop>,<Shortest distance>
# ...
# ...
# Routing Complete
#
# You should also include all of the Self routes in your routing_table argument -- e.g.,  Switch (ID = 4) should include the following entry: 		
# 4,4:4,0
# 0 indicates ‘zero‘ distance
#
# For switches that can’t be reached, the next hop and shortest distance should be ‘-1’ and ‘9999’ respectively. (9999 means infinite distance so that that switch can’t be reached)
#  E.g, If switch=4 cannot reach switch=5, the following should be printed
#  4,5:-1,9999
#
# For any switch that has been killed, do not include the routes that are going out from that switch. 
# One example can be found in the sample log in starter code. 
# After switch 1 is killed, the routing update from the controller does not have routes from switch 1 to other switches.

def routing_table_update(routing_table):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append("Routing Update\n")
    for row in routing_table:
        log.append(f"{row[0]},{row[1]}:{row[2]},{row[3]}\n")
    log.append("Routing Complete\n")
    write_to_log(log)

# "Topology Update: Link Dead" Format is below: (Note: We do not require you to print out Link Alive log in this project)
#
#  Timestamp
#  Link Dead <Switch ID 1>,<Switch ID 2>

def topology_update_link_dead(switch_id_1, switch_id_2):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Link Dead {switch_id_1},{switch_id_2}\n")
    write_to_log(log) 

# "Topology Update: Switch Dead" Format is below:
#
#  Timestamp
#  Switch Dead <Switch ID>

def topology_update_switch_dead(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Dead {switch_id}\n")
    write_to_log(log) 

# "Topology Update: Switch Alive" Format is below:
#
#  Timestamp
#  Switch Alive <Switch ID>

def topology_update_switch_alive(switch_id):
    log = []
    log.append(str(datetime.time(datetime.now())) + "\n")
    log.append(f"Switch Alive {switch_id}\n")
    write_to_log(log) 

def write_to_log(log):
    with open(LOG_FILE, 'a+') as log_file:
        log_file.write("\n\n")
        # Write to log
        log_file.writelines(log)

def extract_routing_table(config_file):
    switch_ports = {}
    with open(config_file, 'r') as config:
        num_of_switches = int(config.readline())
        i = 0
        for line in config:
            switch_id, switch_port, cost = line.split()
            switch_ports[i] = switch_id, switch_port, cost
            i+=1
    return switch_ports, num_of_switches

def bootstrap_register(server_socket, switch_ports, num_of_switches):
    print(f"Waiting on client to send us a message")
    (data, client_addr) = server_socket.recvfrom(1024) # Client address really is a tuple of (ip_addr, port number) from the sender
    print(f"Recieved message from client")
    print(f"Client address is {client_addr}")
    print(f"Client data is '{data.decode('utf-8')}'")
    info = data.decode('utf-8').split()
    return info, client_addr

def main():
    #Check for number of arguments and exit if host/port not provided
    num_args = len(sys.argv)
    if num_args < 3:
        print ("Usage: python controller.py <port> <config file>\n")
        sys.exit(1)
    port = int(sys.argv[1])
    config_file = sys.argv[2]
    switch_dictionary = {}
    switches_online = 0
    # Write your code below or elsewhere in this file
    # So the controller is basically our server and the switches are our clients. We need to create a socket for the controller to listen on, and then we need to create a socket for each switch to send data to the controller on.
    # The controller will listen on the port specified by the user, and the switches will send data to that port. The controller will then send data back to the switches on the port that the switches are listening on.
    print("Creating socket")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # not SOCK_STREAM, which is for TCP. We want UDP, which requires SOCK_DGRAM
    server_socket.bind(('', port)) # 1a of bootstrap process, the controller process binds to a well-known port number, specified as a command line argument.
    
    print(f"We've now bound the socket to {server_socket.getsockname()}, so we can now send messages to the server by specifying its address in sendto")
    # Now we need to read the config file and get the switch IDs and ports that the switches are listening on. We'll store this information in a dictionary, where the key is the switch ID and the value is the port number.
    switch_ports, num_of_switches = extract_routing_table(config_file)
    print(f"Switch ports: {switch_ports}")
    while(switches_online < num_of_switches):
        info, client_addr = bootstrap_register(server_socket, switch_ports, num_of_switches)
        if(info[0] == "REGISTER_REQUEST"):
            register_request_received(info[1])
            switch_dictionary[info[1]] = client_addr
            switches_online+=1
            print(info, client_addr)
    if(switches_online == num_of_switches):
        print("All switches have registered with the controller. Sending routing table to switches.")
        response_ds = {}
        for switch in switch_dictionary:
            print(f"Sending routing table to switch {switch}")
            #instead of the routing table being sent to the switch....
            #1. The id of each neighboring switch is sent to the switch
            #2. A flag indicating whether the switch is alive or dead is sent to the switch (all are alive at start)
            #3. For each live switch, the host/port information of that switch process

            #switch_dictionary[switch] is the address of the switch
            #data structure is as follows: list of switch id's that neighbor the respective switch, a flag indicating whether the switch is alive or dead, and the host/port information of that switch process
            for frame in switch_ports:
                if(frame == switch):
                    response_ds[switch] = frame[1], 1, switch_dictionary[switch]
            print(response_ds)
            print(switch_ports)
            server_socket.sendto(f"ROUTING_TABLE {switch_ports}".encode('UTF-8'), switch_dictionary[switch]) #so the entire routing table is sent to each switch. This isnt really what we want but its a start
            register_response_sent(switch)
            #routing_table_update(switch_ports)

if __name__ == "__main__":
    main()