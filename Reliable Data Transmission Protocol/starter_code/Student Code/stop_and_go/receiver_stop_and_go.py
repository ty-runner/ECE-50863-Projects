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
    max_packet_size -= 8  # Account for the header size
    write_location = cfg.get('receiver', 'write_location')
    #print('Receiver: Waiting for file contents...')
    #listen for contents of file and sending ACKs
    #open file to write to
    with open(write_location, 'wb') as f:
        while True:
            addr, data = recv_monitor.recv(max_packet_size)
            if data == b'':
                break
            if 'data_copy' not in locals() or data_copy != data:
                #print(f'Receiver: Received {len(data)} bytes from id {addr}.')
                #print("Data is: ", data)
                f.write(data)
                print(f'Receiver: Sending ACK to id {addr}.')
                recv_monitor.send(sender_id, b'ACK')
                data_copy = data
    f.close()
    recv_monitor.recv_end('outputs.txt', sender_id)
    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.