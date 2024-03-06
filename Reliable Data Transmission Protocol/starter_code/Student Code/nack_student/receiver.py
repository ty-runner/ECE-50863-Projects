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
		self.window_size: int = int(self.cfg.get('sender', 'window_size'))
		self.receiver_id: int = int(self.cfg.get('receiver', 'id'))
		self.max_packet_size: int = int(self.cfg.get('network', 'MAX_PACKET_SIZE'))
		self.write_location = self.cfg.get('receiver', 'write_location')
		self.next_seq_num: int = 0
		self.recv_monitor.socketfd.settimeout(3)

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
			f.write(data[1])
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
			except:
				print('Receiver: Timeout')
				break
		return ack_nums, data_list
	def recv_process(self) -> None:
		""" Receives packets from sender and sends ACKs """
		missing_packets = set()
		with open(self.write_location, 'wb') as f:
			start = 0
			while True:
				ack_nums = set()
				data_list = {}
				for _ in range(self.window_size):
					try:
						start = time.time()
						packet, recv_id, data = self.recv_parse()
						if recv_id > start + self.window_size:
							print(f"Received packet {recv_id} outside of window, resend NACK.")
							self.send_nack(missing_packets, ack_nums)
						else:
							ack_nums.add(recv_id)
						if data == b'FINAL_PACKET':
							print(f"Received final packet")
							self.write_to_file(f, data_list)
							return
						data_list[recv_id] = data
					except:
						print('Receiver: Timeout')
				if len(ack_nums) == 0:
					break
				elif len(ack_nums) == self.window_size:
					print(f"Received all packets in the window, writing to file")
					self.write_to_file(f, data_list)
					missing_packets = set()
					start += self.window_size
				else:
					missing_packets = set(range(start, start + self.window_size)) - ack_nums
					print(f"Missing packets: {missing_packets}")
					#send cumulative NACK
					self.send_nack(missing_packets, ack_nums)
					#listen for retransmitted packets
					ack_nums, data_list = self.listen_for_retransmit(data_list, ack_nums, missing_packets)
					#sort the data and write to file
					self.write_to_file(f, data_list)

if __name__ == '__main__':
	#basic structure
	#1. Listen for window size number of packets
	#2. store the packets in a buffer
	#3. send cumulative NACK for all missing packets in a window
	print("Receiver starting up!")
	config = sys.argv[1]
	recv = Receiver(config)
	recv.recv_process()
	time.sleep(1)
	recv.recv_monitor.recv_end(recv.write_location, recv.sender_id)
