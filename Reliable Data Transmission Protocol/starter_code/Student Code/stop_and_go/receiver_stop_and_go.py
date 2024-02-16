from monitor import Monitor
import sys
import time

# Config File
import configparser
import socket
timeout = 2  # Timeout period in seconds
if __name__ == '__main__':
    print("Receiver starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    recv_monitor = Monitor(config_path, 'receiver')
    #recv_monitor.socketfd.settimeout(timeout)
    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    sender_id = int(cfg.get('sender', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
    max_packet_size -= 12  # Account for the header size
    write_location = cfg.get('receiver', 'write_location')
    #print('Receiver: Waiting for file contents...')
    #listen for contents of file and sending ACKs
    #open file to write to
    with open(write_location, 'wb') as f:
        data_dict = {}
        past_id = 0
        while True:
            addr, data = recv_monitor.recv(max_packet_size)
            id = int.from_bytes(data[:4], 'big')
            stripped_data = data[4:]
            if stripped_data == b'':
                break
            if 'data_copy' not in locals() or data_copy != data:
                #print(f'Receiver: Received {len(data)} bytes from id {addr}.')
                #print("Data is: ", data)
                id = int.from_bytes(data[:4], 'big')
                print("id is: ", id)
                stripped_data = data[4:]
                print("stripped data is: ", stripped_data)
                data_dict[id] = stripped_data
                print(f'Receiver: Sending ACK to id {addr}.')
                recv_monitor.send(sender_id, b'ACK ' + id.to_bytes(4, 'big'))
                data_copy = data
                past_id = id
        sorted_data_dict = sorted(data_dict.items(), key=lambda x: x[0])
        for key, value in sorted_data_dict:
            print("key: ", key)
            print("data: ", value)
            f.write(value)
    f.close()
    recv_monitor.recv_end("outputs", sender_id)
    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.