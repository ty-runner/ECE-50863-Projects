from monitor import Monitor, format_packet, unformat_packet
import sys
import time

# Config File
import configparser

class Receiver:
	def __init__(self, config) -> None:
		self.config = config
		self.recv_monitor = Monitor(config, 'receiver')
		self.cfg = configparser.RawConfigParser(allow_no_value=True)
		self.cfg.read(config)
		self.sender_id: int = int(self.cfg.get('sender', 'id'))
		self.window_size: int = 0
		self.receiver_id: int = int(self.cfg.get('receiver', 'id'))
		self.max_packet_size: int = int(self.cfg.get('network', 'MAX_PACKET_SIZE'))
		self.write_location = self.cfg.get('receiver', 'write_location')
		self.next_seq_num: int = 0
		self.start = 0
		self.recv_monitor.socketfd.settimeout(2)
		self.num_of_packets = 0
		self.last_window_size = 0
		self.total_packets = 0

	def recv_parse(self) -> tuple[int, bytes]:
		""" Receives packets from sender """
		addr, packet = self.recv_monitor.recv(self.max_packet_size - 50)
		packet = unformat_packet(packet)[1]
		seq_num = int.from_bytes(packet[:4], byteorder='big')  # Convert to correct byte order
		#print(f"Received packet {seq_num}.")
		return packet, seq_num, packet[4:]
	def write_to_file(self, f, data_list) -> None:
		""" Writes data to file """
		#make sure the data is sorted
		data_list = sorted(data_list.items(), key=lambda x: x[0])
		for data in data_list:
			print(data[0])
			if data[1] != b'FINAL_PACKET':
				f.write(data[1])
			else:
				packet = b'FINAL_PACKET'
				self.recv_monitor.send(self.sender_id, format_packet(self.receiver_id, self.sender_id, packet))
				return
		print("Wrote to file")
	def send_nack(self, missing_packets: set[int], ack_nums) -> None:
		""" Sends NACK to sender for missing packets """
		#send cumulative NACK
		if len(missing_packets) == 0:
			return
		missing_packets = sorted(missing_packets)
		received_size = len(ack_nums) - len(missing_packets)
		packet = (received_size).to_bytes(4, byteorder='big')
		for miss in missing_packets:
			print(f"Sending NACK for packet {miss}.")
			packet += (miss).to_bytes(4, byteorder='big')
		self.recv_monitor.send(self.sender_id, format_packet(self.receiver_id, self.sender_id, packet))
		print(f"Sent NACK for packets {missing_packets}.")
	def listen_for_retransmit(self, data_list, ack_nums, missing_packets):
		""" Listens for retransmitted packets """
		while True:
			try:
				packet, recv_id, data = self.recv_parse()
				if recv_id in missing_packets:
					print(f"Received retransmitted packet {recv_id}.")
					ack_nums.add(recv_id)
					data_list[recv_id] = data
					missing_packets.remove(recv_id)
					if len(missing_packets) == 0:
						break
			except:
				print('Receiver: Timeout')
				self.send_nack(missing_packets, ack_nums)

				#ack_nums, data_list = self.listen_for_retransmit(data_list, ack_nums, missing_packets)
				#break
		return ack_nums, data_list
	def receive_num_of_packets(self):
		""" Receives the number of packets to expect """
		data = None
		while data is None:
			try:
				packet, recv_id, data = self.recv_parse()
				#num_of_packets = int.from_bytes(recv_id, byteorder='big')
				self.num_of_packets = int.from_bytes(data, byteorder='big')  # Convert to correct byte order
				print(f"Received number of packets: {self.num_of_packets}.")
				self.window_size = recv_id
				print(f"Received window size: {self.window_size}.")
				self.last_window_size = self.num_of_packets % self.window_size
				print(f"Last window size: {self.last_window_size}.")
				self.total_packets = self.num_of_packets
			except:
				print('Receiver: Timeout')

	def recv_process(self) -> None:
		""" Receives packets from sender and sends ACKs """
		missing_packets = set()
		with open(self.write_location, 'wb') as f:
			while True:
				ack_nums = set()
				data_list = {}
				for _ in range(min(self.window_size, self.num_of_packets)):
					try:
						packet, recv_id, data = self.recv_parse()
						if recv_id > self.start + min(self.window_size-1, self.num_of_packets):
							print(f"Received packet {recv_id} outside of window, resend NACK.")
							self.send_nack(missing_packets, ack_nums)
						elif recv_id < self.start:
							print(f"Received duplicate {recv_id}, ignoring.")
						else:
							ack_nums.add(recv_id)
							data_list[recv_id] = data
					except:
						print('Receiver: Timeout')
				if len(ack_nums) == 0:
					break
				elif ((list(ack_nums)[-1] - list(ack_nums)[0]) == self.window_size - 1) and (len(ack_nums) == self.window_size):
					print(f"Received all packets in the window, writing to file")
					self.write_to_file(f, data_list)
					missing_packets = set()
					self.start += self.window_size
					self.num_of_packets -= self.window_size
					#self.num_of_packets -= self.window_size
					print(f"Moving window to {self.start}.")
					#print(f"Number of packets left: {self.num_of_packets}.")
				else:
					print(self.start, self.start + self.window_size-1)
					end = self.start + min(self.window_size, self.num_of_packets)
					print(f"End of window {end}.")
					print(f"Received packets {ack_nums}.")
					print(f"Current range: {range(self.start, end-1)}.")
					if len(ack_nums) == self.last_window_size-1 and data_list[list(ack_nums)[-1]] == b'FINAL_PACKET':
						print(f"Received all packets in the window, writing to file")
						self.write_to_file(f, data_list)
						missing_packets = set()
						self.num_of_packets -= self.window_size
						print(f"Number of packets left: {self.num_of_packets}.")
						return
					missing_packets = set(range(self.start, end)) - set(ack_nums)
					print(f"Missing packets: {missing_packets}")
					#send cumulative NACK
					if len(missing_packets) != 0:
						self.send_nack(missing_packets, ack_nums)
						#listen for retransmitted packets
						ack_nums, data_list = self.listen_for_retransmit(data_list, ack_nums, missing_packets)
					#sort the data and write to file
					self.write_to_file(f, data_list)
					self.start += self.window_size
					self.num_of_packets -= self.window_size
					print(f"num of packets left: {self.num_of_packets}.")
					if self.start > self.total_packets:
						print("ENTERED")
						if list(ack_nums)[-1] == self.num_of_packets-1:
							return
						else:
							self.send_nack(missing_packets, ack_nums)

if __name__ == '__main__':
	#basic structure
	#1. Listen for window size number of packets
	#2. store the packets in a buffer
	#3. send cumulative NACK for all missing packets in a window
	print("Receiver starting up!")
	config = sys.argv[1]
	recv = Receiver(config)
	recv.receive_num_of_packets()
	recv.recv_process()
	time.sleep(1)
	recv.recv_monitor.recv_end(recv.write_location, recv.sender_id)
