# ECE 50863 Project 1

The switches and the controller emulate a topology specified in a topology configuration file. We begin by describing the format of the configuration file, next discuss the bootstrap process (the action performed by each switch process at the start of execution), path computation (how the controller computes routing tables), and the periodic actions that must be continually performed by the switch and the controller.

## Bootstrap Process
The bootstrap process refers to how switches register with the controller, as well as learn about each other. 
Note: The bootstrap process must also enable the controller process, and each of the switch processes, to learn each other’s host/port information (hostname and UDP port number information), so communication using socket programming is feasible.

1.	The controller and switch processes are provided with information using command line arguments (we require the command line arguments follow a required format discussed under ‘Running your Code and Important Requirements’)
  a.	The controller process binds to a well-known port number
  b.	Each switch process is provided with its own id, as well as the hostname and port number, that the controller process runs on, as command line arguments. 

2.	When a switch (for instance, with ID = 4) joins the system, it contacts the controller with a Register Request, along with its id. The controller learns the host/port information of the switch from this message.

3.	Once all switches have registered, the controller responds with a Register Response message to each switch which includes the following information
  a.	The id of each neighboring switch
  b.	a flag indicating whether the neighbor is alive or not (initially, all switches are alive)
  c.	for each live switch, the host/port information of that switch process.

## Path Computations
1.	Once all switches have registered, the controller computes paths between each source-destination pair using the shortest path algorithm.
2.	Once path computation is completed, the controller sends each switch its “routing table” using a Route Update message. This table sent to switch A includes an entry for every switch (including switch A itself), and the next hop to reach every destination. The self-entry is indicated by an zero (=0) distance. If a switch can’t be reached from the current switch, then the next hop is set to -1 and the distance is set to 9999.

*Periodic Operations*
Each switch and the controller must perform a set of operations at regular intervals to ensure smooth working of the network. 
Switch Operations
1.	Each switch sends a Keep Alive message every K seconds to each of the neighboring switches that it thinks is ‘alive’.
2.	Each switch sends a Topology Update message to the controller every K seconds. The Topology Update message includes a set of ‘live’ neighbors of that switch.
3.	If a switch A has not received a Keep Alive message from a neighboring switch B for TIMEOUT seconds, then switch A declares the link connecting it to switch B as down. Immediately, it sends a Topology Update message to the controller sending the controller its updated view of the list of ‘live’ neighbors.
4.	Once a switch A receives a Keep Alive message from a neighboring switch B that it previously considered unreachable, it immediately marks that neighbor alive, updates the host/port information of the switch if needed, and sends a Topology Update to the controller indicating its revised list of ’live’ neighbors.

IMPORTANT: To be compatible with the auto-grader, we require that you use particular values of K and TIMEOUT as mentioned under the “Running your Code and Important Requirements” section.
*Controller Operations*
1.	If the controller does not receive a Topology Update message from a switch for TIMEOUT seconds, then it considers that switch ‘dead’, and updates its topology. 
2.	If a controller receives a Register Request message from a switch it previously considered as ‘dead’, then it responds appropriately and marks it as ‘alive’.
3.	If a controller receives a Topology Update message from a switch that indicates a neighbor is no longer reachable, then the controller updates its topology to reflect that link as unusable.
4.	When a controller detects a change in the topology, it performs a recomputation of paths using the shortest path algorithm described above. It then sends a Route Update message to all switches as described previously.

## Logging
We REQUIRE that your switch and controller processes must log messages in a format exactly matching what the auto-grader requires. The logfile names must also match what the auto-grader expects. No additional messages should be printed.

To help you with generating the right format for the logs, in the starter code, we have created a starter version of controller.py and switch.py for you. Those two files contain various log functions that you must use. Each log function corresponds to a type of log message that will be explained below. We strongly recommend that you use those functions because the auto-grader is quite picky about exact log formats. If you choose not to use those functions, we won’t be able to award credit for test cases that fail owing to minor logging discrepancies.
Switch Process
Switch Process must log
1.	when a Register Request is sent, 
2.	when the Register Response is received, 
3.	when any neighboring switches are considered unreachable, 
4.	when a previously unreachable switch is now reachable
5.	The switch must also log the routing table that it gets from the controller each time that the table is updated.
Log File name
  This must be switch<Switch-ID>.log

E.g., For Switch (ID = 4)
  switch4.log
Format for Switch Logs
Format for each type of log messages is shown in comments beside their corresponding log functions. Please refer to the starter code.


Controller Process
The Controller process must log 
1.	When a Register Request is received,
2.	When all the Register Responses are sent (send one register response to each switch),
3.	When it detects a change in topology (a switch or a link is down or up),
4.	Whenever it recomputes (or computes for the first time) the routes. 
Format for Controller Logs
Format for each type of log messages is shown in comments beside their corresponding log functions. Please refer to the starter code.

Controller Log File name
  This must be Controller.log




Note: To reduce log output, please do not print messages when Keep Alive messages are sent or received. We also do not have log function for this.
Sample logs are available with the starter code. The sample log file is the situation where Config/graph_3.txt is used. Therefore, you will find one controller log file Controller.log and three switch log files switch0.log, switch1.log, and switch2.log. After all the switches know the initial topology, switch 1 is killed, and a new topology is calculated by the controller and sent out to the switches.


## Running your code and Important Requirements
We must be able to run the Controller and Switch python files by running:
  python controller.py [controller port] [config file]
  python switch.py <switchID> <controller hostname> <controller port> -f <neighbor ID>
The Controller should be executed first in a separate terminal. While it is running each switch should be launched in a separate terminal with the Switch ID, Controller hostname and the port.
Important Requirements:
To be compatible with the auto-grader, the following are mandatory requirements:
1)	You must support command line arguments in the above format. Note that the “-f” flag for the switch is a parameter for link failures (See ‘Simulating Link Failure’), and we must be able to run your code with and without this flag.
2)	Please use K = 2; TIMEOUT = 3* K  (recall these parameters pertain to timers related to Periodic operations of the switch and the Controller)
As mentioned earlier, you are strongly recommended to use the logging functions that we provide.
