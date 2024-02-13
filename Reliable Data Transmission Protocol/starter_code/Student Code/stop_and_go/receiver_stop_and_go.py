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

    # Exchange messages!
    addr, data = recv_monitor.recv(max_packet_size)
    print(f'Receiver: Got message from id {addr}: {data}')
    print('Receiver: Responding with "Hello, Sender!".')
    recv_monitor.send(sender_id, b'Hello, Sender!')

    #listen for contents of file and sending ACKs
    while True:
        addr, data = recv_monitor.recv(max_packet_size)
        if data == b'':
            break
        print(f'Receiver: Received {len(data)} bytes from id {addr}.')
        print("Data is: ", data)
        print(f'Receiver: Sending ACK to id {addr}.')
        recv_monitor.send(sender_id, b'ACK')
    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
    recv_monitor.recv_end('received_file', sender_id)