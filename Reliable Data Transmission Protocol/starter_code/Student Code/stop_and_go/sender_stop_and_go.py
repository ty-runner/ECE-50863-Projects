from monitor import Monitor
import sys

# Config File
import configparser
import time

timeout = 5  # Timeout period in seconds

if __name__ == '__main__':
    print("Sender starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    send_monitor = Monitor(config_path, 'sender')
    
    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    receiver_id = int(cfg.get('receiver', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
    max_packet_size -= 8  # Account for the header size

    # Exchange messages!
    #send the file in max_packet_size chunks
    with open(file_to_send, 'rb') as f:
        send_count = 0
        while True:
            chunk = f.read(max_packet_size)
            if not chunk:
                send_monitor.send(receiver_id, b'')
                break
            if send_count == 0:
                send_monitor.send(receiver_id, chunk)
            else:
                # receive ACK from receiver
                ack_received = False
                start_time = time.time()
                while not ack_received:
                    addr, data = send_monitor.recv(max_packet_size)
                    if data == b'ACK':
                        print(f'Sender: Got ACK from id {addr}: {data}')
                        print(f'Sender: Sending file {file_to_send} to receiver.')
                        send_monitor.send(receiver_id, chunk)
                        ack_received = True
                    elif time.time() - start_time >= timeout:
                        print(f'Sender: Timeout occurred. Retransmitting packet...')
                        send_monitor.send(receiver_id, chunk)
                        start_time = time.time()
            #wait TIMEOUT seconds for ACK
            send_count += 1
    print(f'Sender: File {file_to_send} sent to receiver.')
    f.close()
    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
    time.sleep(2)
    send_monitor.send_end(receiver_id)