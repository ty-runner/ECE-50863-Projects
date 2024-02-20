from monitor import Monitor
import sys

# Config File
import configparser
import time
import socket
timeout = 0.5  # Timeout period in seconds

if __name__ == '__main__':
    print("Sender starting up!")
    config_path = sys.argv[1]

    # Initialize sender monitor
    send_monitor = Monitor(config_path, 'sender')
    send_monitor.socketfd.settimeout(timeout)
    #send_monitor.socketfd.setblocking(False)
    # Parse config file
    cfg = configparser.RawConfigParser(allow_no_value=True)
    cfg.read(config_path)
    receiver_id = int(cfg.get('receiver', 'id'))
    file_to_send = cfg.get('nodes', 'file_to_send')
    max_packet_size = int(cfg.get('network', 'MAX_PACKET_SIZE'))
    max_packet_size -= 12  # Account for the header size
    #addr, data = send_monitor.recv(max_packet_size)

    # Exchange messages!
    #send the file in max_packet_size chunks
    with open(file_to_send, 'rb') as f:
        send_count = 0
        first_packet = True
        chunk_copy = b''
        while True:
            chunk = f.read(max_packet_size)
            if not chunk:
                header = send_count.to_bytes(4, byteorder='big')
                send_monitor.send(receiver_id, b'')
                break
            if first_packet:
                header = send_count.to_bytes(4, byteorder='big')
                send_monitor.send(receiver_id, header + chunk)
                send_count += 1
                first_packet = False
                chunk_copy = chunk
            else:
                # receive ACK from receiver
                ack_received = False
                start_time = time.time()
                while not ack_received:
                    try:
                        addr, data = send_monitor.recv(max_packet_size)
                    except socket.timeout:
                        #print(f'Sender: Timeout occurred. Retransmitting packet...')
                        header = (send_count-1).to_bytes(4, byteorder='big')
                        #print(f'Sender: Sending header issue {send_count-1}...')
                        send_monitor.send(receiver_id, header + chunk_copy)
                        #print(f'Retransmitting  {chunk_copy}...')
                        start_time = time.time()
                        data = b''
                    if data == b'ACK' + (send_count-1).to_bytes(4, byteorder='big'):
                        #print(f'Sender: Got ACK from id {addr}: {data}')
                        #print(f'Sender: Sending header true {send_count}...')
                        header = send_count.to_bytes(4, byteorder='big')
                        send_monitor.send(receiver_id, header + chunk)
                        ack_received = True
                        send_count += 1
                        chunk_copy = chunk
                    else:
                        #print(send_count)
                        print(f'Sender: Got unexpected data from id: {int.from_bytes(data[3:7], byteorder="big")}. expected: {send_count-1}...')
                        #print(send_count, int(data[3:7]))
                        chunk_copy = chunk
            #wait TIMEOUT seconds for ACK
    print(f'Sender: File {file_to_send} sent to receiver.')
    f.close()
    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
    time.sleep(1.5)
    send_monitor.send_end(receiver_id)