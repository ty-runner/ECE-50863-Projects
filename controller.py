#!/usr/bin/env python

"""This is the Controller Starter Code for ECE50863 Lab Project 1
Author: Xin Du
Email: du201@purdue.edu
Last Modified Date: December 9th, 2021
"""

import sys
import heapq
import socket
import time
import threading
from datetime import date, datetime

# Please do not modify the name of the log file, otherwise you will lose points because the grader won't be able to find your log file
LOG_FILE = "Controller.log"
K = 5
TIMEOUT = 15
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

def create_adjacency_list_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()[1:]  # Skip the first line

    graph = [tuple(map(int, line.split())) for line in lines]
    adjacency_list = create_adjacency_list(graph)

    return adjacency_list
def create_adjacency_list(graph):
    adjacency_list = {}

    # Create a set to keep track of all unique nodes
    nodes = set()
    for edge in graph:
        node1, node2, distance = edge
        nodes.add(node1)
        nodes.add(node2)

    # Sort the nodes in ascending order
    sorted_nodes = sorted(nodes)

    # Create the adjacency list with sorted nodes
    for node in sorted_nodes:
        adjacency_list[node] = []

    # Add edges to the adjacency list
    for edge in graph:
        node1, node2, distance = edge

        # Add node2 to the neighbors of node1
        adjacency_list[node1].append((node2, distance))

        # Add node1 to the neighbors of node2 (because the graph is undirected)
        adjacency_list[node2].append((node1, distance))

    # Sort neighbors for each node in ascending order
    for node in adjacency_list:
        adjacency_list[node] = sorted(adjacency_list[node])

    return adjacency_list
def add_self_to_adjacency_list(adjacency_list, switch_id):
    adjacency_list[switch_id].append((switch_id, 0))
    for node in adjacency_list:
        adjacency_list[node] = sorted(adjacency_list[node])
    return adjacency_list

def dijkstra(adjacency_list, start_vertex):
    distances = {vertex: float('infinity') for vertex in adjacency_list}
    distances[start_vertex] = 0
    next_hop = {vertex: None for vertex in adjacency_list}

    priority_queue = [(0, start_vertex)]

    while priority_queue:
        current_distance, current_vertex = heapq.heappop(priority_queue)

        for neighbor, weight in adjacency_list[current_vertex]:
            distance = current_distance + weight

            # Update distances and next hop
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                # Update next hop based on the number of hops
                if distances[neighbor] == weight:
                    # Single hop path, set next hop as the destination
                    next_hop[neighbor] = neighbor
                else:
                    # Multi-hop path, set next hop as the second node
                    next_hop[neighbor] = current_vertex

                heapq.heappush(priority_queue, (distance, neighbor))

    # Set next hop and distance to -1 and 9999 respectively for unreachable destinations
    for vertex in adjacency_list:
        if distances[vertex] == float('infinity'):
            next_hop[vertex] = -1
            distances[vertex] = 9999

    return distances, next_hop
def listen_for_switches(server_socket, switch_dictionary):
    client_addr = []
    for switch in switch_dictionary:
        print(f"Listening for switch {switch}")
        (data, addr) = server_socket.recvfrom(1024)
        if addr not in client_addr:
            client_addr.append(addr)
        print(data.decode('utf-8'))
    if len(client_addr) == len(switch_dictionary):
        print("All switches have sent their routing tables to the controller")
    else:
        print("Not all switches have sent their routing tables to the controller")
        #find what switch hasnt sent their topology
        for switch in switch_dictionary:
            if switch_dictionary[switch] not in client_addr:
                print(f"Switch {switch} has not sent their topology to the controller")
                topology_update_switch_dead(int(switch))
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
    adjacency_list = create_adjacency_list_from_file(config_file)
    while(switches_online < num_of_switches):
        info, client_addr = bootstrap_register(server_socket, switch_ports, num_of_switches)
        if(info[0] == "REGISTER_REQUEST"):
            register_request_received(info[1])
            switch_dictionary[int(info[1])] = client_addr
            switches_online+=1
    if(switches_online == num_of_switches):
        print("All switches have registered with the controller. Sending routing table to switches.")
        response_ds = {}
        neighbors = {}
        for switch in switch_dictionary:
            print(f"Sending routing table to switch {switch}")
            #instead of the routing table being sent to the switch....
            #1. The id of each neighboring switch is sent to the switch
            #2. A flag indicating whether the switch is alive or dead is sent to the switch (all are alive at start)
            #3. For each live switch, the host/port information of that switch process

            #switch_dictionary[switch] is the address of the switch
            #data structure is as follows: list of switch id's that neighbor the respective switch, a flag indicating whether the switch is alive or dead, and the host/port information of that switch process

            #lets fetch the neighbors of the switch
            for node in adjacency_list:
                if int(node) == int(switch):
                    neighbors[node] = [neighbor[0] for neighbor in adjacency_list[node]]
            for index in neighbors.keys():
                index = int(index)
                response_ds[index] = [neighbors[index], 1, [switch_dictionary[neighbor] for neighbor in neighbors[index]]]
            print(switch_dictionary[int(switch)])
            #neighbors
            server_socket.sendto(f"RESPONSE_NEIGHBORS {response_ds[int(switch)][0]}".encode('UTF-8'), switch_dictionary[int(switch)]) #so the entire routing table is sent to each switch. This isnt really what we want but its a start
            #alive flag
            server_socket.sendto(f"RESPONSE_ALIVE_FLAG {response_ds[int(switch)][1]}".encode('UTF-8'), switch_dictionary[int(switch)]) #so the entire routing table is sent to each switch. This isnt really what we want but its a start
            #host/port information
            server_socket.sendto(f"RESPONSE_NEIGHBOR_INFO {response_ds[int(switch)][2]}".encode('UTF-8'), switch_dictionary[int(switch)]) #so the entire routing table is sent to each switch. This isnt really what we want but its a start
            register_response_sent(switch)
        #that completes the bootstrap process. Now we need to send the initial routing table to each switch. This routing table is of the format src, dest, next hop, distance
        
        #the next hop and distance are calculated using dijkstras algorithm
        for switch in adjacency_list:
            adjacency_list = add_self_to_adjacency_list(adjacency_list, switch)
        #we now have an adjacency list with the self entry added to each switch
        routing_table = []
        dijkstra_entries = {}
        for switch in adjacency_list:
            #print(f"Switch {switch} neighbors: {adjacency_list[switch]}")
            dijkstra_result, next_hop_dict = dijkstra(adjacency_list, switch)
            dijkstra_entries[switch] = dijkstra_result
            #print(f"Dijkstra result for switch {switch} is {dijkstra_result}")
            #print(f"Next hop for switch {switch} is {next_hop_dict}")
            for destination, distance in dijkstra_result.items():
                if destination != switch:
                    next_hop = next_hop_dict[destination]
                    routing_table.append([switch, destination, next_hop, distance])
                else:
                    routing_table.append([switch, destination, destination, 0]) #self entry
        #print(routing_table)
        #issues: the next hop if is the node right before destination, if there are 3 hops, it is incorrect, check dijkstra func
        # Test the function
        routing_table_update(routing_table)
        routing_table_entries = {}
        for switch in switch_dictionary:
            routing_table_entries[switch] = []
            for entry in routing_table:
                if entry[0] == switch:
                    routing_table_entries[switch].append(f"{entry[0]},{entry[1]}:{entry[2]}")
        for switch in switch_dictionary:
            server_socket.sendto(f"RESPONSE_ROUTING_TABLE_BATCH {routing_table_entries[switch]}".encode('UTF-8'), switch_dictionary[switch])
        #we have now sent the initial routing table to each switch
        #now we need to listen for updates from the switches
        listen_for_switches(server_socket, switch_dictionary)
        
if __name__ == "__main__":
    main()