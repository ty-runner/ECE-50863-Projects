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
        while True:
            addr, data = recv_monitor.recv(max_packet_size)
            if data == b'':
                break
            #print(f'Receiver: Received {len(data)} bytes from id {addr}.')
            id = int.from_bytes(data[:4], byteorder='big')
            print(f'Receiver: Received id {id}.')
            data = data[4:]
            print("Data is: ", data)
            if received_count > id:
                received_count = id
            else:
                f.write(data)
            #print(f'Receiver: Sending ACK to id {addr}.')
            recv_monitor.send(sender_id, b'ACK' + received_count.to_bytes(4, byteorder='big'))
            received_count += 1
    f.close()
    recv_monitor.recv_end("write_location", sender_id)
    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.