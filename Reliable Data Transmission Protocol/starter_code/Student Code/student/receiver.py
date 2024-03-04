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
		print(f"Received {len(packet)} bytes from id {addr}.")
		packet = unformat_packet(packet)[1]
		seq_num = int.from_bytes(packet[:4], byteorder='big')  # Convert to correct byte order
		return seq_num, packet[4:]
	
	def recv_process(self) -> None:
		""" Receives packets from sender and sends ACKs """
		with open(self.write_location, 'wb') as f:
			while True:
				try:
					recv_id, data = self.recv_parse()
					if recv_id == self.next_seq_num:
						f.write(data)
						print(f"Received packet {recv_id}.")
						self.recv_monitor.send(self.sender_id, format_packet(self.receiver_id, self.sender_id, self.next_seq_num.to_bytes(4, byteorder='big')))
						self.next_seq_num += 1
					elif data == b'':
						print("Received all packets.")
						break
				except:
					print('Receiver: Timeout')
			self.recv_monitor.recv_end("self.write_location", self.sender_id)

if __name__ == '__main__':
	print("Receiver starting up!")
	config = sys.argv[1]
	recv = Receiver(config)
	recv.recv_process()
