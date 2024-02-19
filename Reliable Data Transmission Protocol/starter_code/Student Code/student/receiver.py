from monitor import Monitor
import sys
import time

# Config File
import configparser

if __name__ == '__main__':
	print("Receiver starting up!")
	config_path = sys.argv[1]

	# Initialize sender monitor
	recv_monitor = Monitor(config_path, 'receiver')
	
	# Parse config file
	cfg = configparser.RawConfigParser(allow_no_value=True)
	cfg.read(config_path)
	sender_id = int(cfg.get('sender', 'id'))
	file_to_send = cfg.get('nodes', 'file_to_send')
	max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
	max_packet_size -= 12  # Account for the header size
	write_location = cfg.get('receiver', 'write_location')
	print('Receiver: Waiting for file contents...')
	#listen for contents of file and sending ACKs
	#open file to write to
	with open(write_location, 'wb') as f:
		received_count = 0
		received_list = []
		while True:
			# Receive packet from sender
			addr, packet = recv_monitor.recv(max_packet_size)
			
			# Check if packet is the end signal
			if packet == b'':
				print('Receiver: End signal received from sender')
				break
			
			# Extract sequence number and data from packet
			print(f'Packet is {packet}.')
			seq_num = int.from_bytes(packet[:4], byteorder='big')
			data = packet[4:]
			
			# Check if packet is in the window
			if seq_num >= received_count:
				# Check if packet has already been received
				if seq_num not in received_list:
					# Write data to file
					f.write(data)
					
					# Update received count and list
					received_count += 1
					received_list.append(seq_num)
					
					# Send ACK to sender
					ack_packet = seq_num.to_bytes(4, byteorder='big')
					recv_monitor.send(sender_id, b'ACK' + packet[:4])
					print(f'Receiver: ACK{seq_num} sent to sender')
				else:
					print(f'Receiver: Duplicate packet received with sequence number {seq_num}')
			else:
				print(f'Receiver: Packet received with sequence number {seq_num} is not in the window')
		
	# Send end signal to sender
	f.close()
	time.sleep(1)
	recv_monitor.recv_end("write_location", sender_id)
	# Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
