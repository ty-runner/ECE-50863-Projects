from monitor import Monitor, format_packet, unformat_packet
import sys

# Config File
import configparser
import time
import socket
timeout = 0.5  # Timeout period in seconds

class Sender:
	def __init__(self, config):
		self.config = config
		self.send_monitor = Monitor(config, 'sender')
		self.cfg = configparser.RawConfigParser(allow_no_value=True)
		self.cfg.read(config)
		self.send_monitor.socketfd.settimeout(timeout)
		self.ack_nums = []
		self.sender_id: int = int(self.cfg.get('sender', 'id'))
		self.receiver_id: int = int(self.cfg.get('receiver', 'id'))
		self.window_size: int = int(self.cfg.get('sender', 'window_size'))
		self.file_to_send = self.cfg.get('nodes', 'file_to_send')
		self.max_packet_size = int(self.cfg.get('network', 'MAX_PACKET_SIZE'))
		self.window_start = 0
		self.window_end = self.window_start + self.window_size - 1
		self.data = []
		self.num_of_packets = 0
	def create_data_array(self, file_to_send, max_packet_size):
		""" Creates an array of data packets from the file to send """
		data = []
		with open(file_to_send, 'rb') as f:
			header_count = 0
			while True:
				chunk = f.read(max_packet_size - 100)
				if not chunk:
					data.append(b'')
					break
				header = header_count.to_bytes(4, byteorder='big')
				data.append(header + chunk)
				header_count += 1
		return data
	def extract_seq_num(data):
		""" Extracts the sequence number from the packet """
		return int.from_bytes(data[3:7], byteorder='big')

	def retransmit_packets(self, send_monitor, receiver_id, window_start, window_end, data, ack_nums):
		""" Retransmits packets in the window """
		for i in range(	window_start, window_end):
			if i not in ack_nums:
				packet = data[i]
				print(f"Retransmitting packet {i}.")
				send_monitor.send(receiver_id, format_packet(self.sender_id, receiver_id, packet))
	def send_process(self) -> None:
		""" Sends packets in the window """
		window_start = 0
		while window_start < len(self.data) - 1:
			window_end = window_start + self.window_size
			if window_end > len(self.data):
				window_end = len(self.data)
			for seq_num in range(window_start, window_end):
				packet = self.data[seq_num]
				time.sleep(0.005)
				print(f"Sending packet {seq_num}.")
				self.send_monitor.send(self.receiver_id, format_packet(self.sender_id, self.receiver_id, packet))
			for _ in range(window_start, window_end):
				ACK = self.listen_for_ack(window_start, self.num_of_packets)
				print(f"Received ACK {ACK}.")
				if ACK is not None:
					window_start = ACK + 1
					self.ack_nums.append(ACK)
				else:
					print("Timeout: Retransmitting packets.")
					self.retransmit_packets(self.send_monitor, self.receiver_id, window_start, window_end, self.data, self.ack_nums)
	def listen_for_ack(self, window_start, num_of_packets):
		""" Listens for an ACK """
		while True:
			try:
				addr, data = self.send_monitor.recv(self.max_packet_size - 50)
				data = unformat_packet(data)[1]
				seq_id = int.from_bytes(data, byteorder='big')
				if seq_id == window_start:
					return seq_id
				elif seq_id >= num_of_packets:
					return seq_id
			except socket.timeout:
				return None
			except:
				return None
	def begin_send(self):
		""" Starts the sending process """
		self.data = self.create_data_array(self.file_to_send, self.max_packet_size)
		self.num_of_packets = len(self.data)
		print(f"Number of packets: {self.num_of_packets}.")
		self.send_process()
		time.sleep(2)
		self.send_monitor.send_end(self.receiver_id)
if __name__ == '__main__':
	print("Sender starting up!")
	config = sys.argv[1]
	sender = Sender(config)
	sender.begin_send()