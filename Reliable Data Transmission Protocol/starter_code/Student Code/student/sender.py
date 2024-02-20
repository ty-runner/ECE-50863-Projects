from monitor import Monitor
import sys

# Config File
import configparser
import time
import socket
timeout = 0.75  # Timeout period in seconds

def create_data_array(file_to_send, max_packet_size):
	""" Creates an array of data packets from the file to send """
	data = []
	with open(file_to_send, 'rb') as f:
		header_count = 0
		while True:
			chunk = f.read(max_packet_size)
			if not chunk:
				data.append(b'')
				break
			header = header_count.to_bytes(4, byteorder='big')
			data.append(header + chunk)
			header_count += 1
	f.close()
	return data
def extract_seq_num(data):
	""" Extracts the sequence number from the packet """
	return int.from_bytes(data[3:7], byteorder='big')

def retransmit_packets(send_monitor, receiver_id, window_start, window_end, data, ack_nums):
	""" Retransmits packets in the window """
	for i in range(	window_start, window_end):
		if i not in ack_nums:
			packet = data[i]
			if type(packet) != bytes:
				packet = packet.to_bytes(4, byteorder='big')
			elif packet == b'' or packet != None:
				send_monitor.send(receiver_id, packet)
if __name__ == '__main__':
	print("Sender starting up!")
	config_path = sys.argv[1]
	ack_nums = []
	# Initialize sender monitor
	send_monitor = Monitor(config_path, 'sender')
	send_monitor.socketfd.settimeout(timeout)
	#send_monitor.socketfd.setblocking(False)
	# Parse config file
	cfg = configparser.RawConfigParser(allow_no_value=True)
	cfg.read(config_path)
	receiver_id = int(cfg.get('receiver', 'id'))
	file_to_send = cfg.get('nodes', 'file_to_send')
	max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
	max_packet_size -= 12  # Account for the header size
	window_size = int(cfg.get('sender', 'window_size'))
	window_size = 6
	#addr, data = send_monitor.recv(max_packet_size)
	data = create_data_array(file_to_send, max_packet_size)
	print(len(data))
	window_start = 0  # Start index of the window
	window_end = window_start + window_size - 1  # End index of the window
	# For sliding window, we send packets in the window and wait for acks, as we receive acks, we slide the window
	while window_start < len(data)-1:
		# Send packets within the window
		if window_end > len(data):
			window_end = len(data) - 1
		#send all packets in the window
		for i in range(window_start, window_end):
			packet = data[i]
			#print(i)
			#print(f'Packet is {packet}.')
			#print(f'type of packet is {type(packet)}.')
			if type(packet) != bytes:
				packet = packet.to_bytes(4, byteorder='big')
			elif packet == b'' or packet != None:
				send_monitor.send(receiver_id, packet)

		# Wait for acknowledgements
		for i in range(window_start, window_end):
			if window_start == len(data)-1:
				break
			if window_end > len(data):
				window_end = len(data) - 1
			try:
				addr, packet = send_monitor.recv(max_packet_size)
			except socket.timeout:
				#print(f'Sender: Timeout occurred. Retransmitting packet...')
				retransmit_packets(send_monitor, receiver_id, window_start, window_end, data, ack_nums)
			if packet is not None:
				# Process the acknowledgement
				ack_seq_num = extract_seq_num(packet)
				if ack_seq_num == window_start:
					# Move the window forward
					window_start += 1
					window_end += 1
					# print(f'window_start is {window_start}.')
					ack_nums.append(ack_seq_num)
					break
	# print(ack_nums)
	# print(f'Sender: File {file_to_send} sent to receiver.')
	# Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
	time.sleep(0.5)
	send_monitor.send_end(receiver_id)
