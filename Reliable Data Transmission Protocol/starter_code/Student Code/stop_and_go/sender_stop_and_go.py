from monitor import Monitor
import sys

# Config File
import configparser
import time
import socket
timeout = 1  # Timeout period in seconds

async def listen(send_monitor, max_packet_size):
    addr, data = await send_monitor.recv(max_packet_size)
    return addr, data
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
        while True:
            chunk = f.read(max_packet_size)
            if not chunk:
                header = send_count.to_bytes(4, 'big')  # Convert send_count to 4-byte header
                send_monitor.send(receiver_id, header + b'')
                break
            if send_count == 0:
                header = send_count.to_bytes(4, 'big')  # Convert send_count to 4-byte header
                send_monitor.send(receiver_id, header + chunk)
                print("send count: ", send_count)
                send_count += 1
            else:
                # receive ACK from receiver
                ack_received = False
                start_time = time.time()
                data = b''
                while not ack_received:
                    try:
                        addr, data = send_monitor.recv(max_packet_size)
                    except socket.timeout:
                        print(f'Sender: Timeout occurred. Retransmitting packet...')
                        header = send_count.to_bytes(4, 'big')  # Convert send_count to 4-byte header
                        send_monitor.send(receiver_id, header + chunk)
                        print("send count: ", send_count)
                        print("chunk of data sent: ", chunk)
                        start_time = time.time()
                    if data == b'ACK':
                        #print(f'Sender: Got ACK from id {addr}: {data}')
                        #print(f'Sender: Sending file {file_to_send} to receiver.')
                        header = send_count.to_bytes(4, 'big')  # Convert send_count to 4-byte header
                        send_monitor.send(receiver_id, header + chunk)
                        print("send count: ", send_count)
                        ack_received = True
                        send_count += 1
                        start_time = time.time()
                    if time.time() - start_time > timeout:
                        print(f'Sender: Timeout occurred. Retransmitting packet...')
                        header = send_count.to_bytes(4, 'big')
                        send_monitor.send(receiver_id, header + chunk)
                        start_time = time.time()

            #wait TIMEOUT seconds for ACK
    print(f'Sender: File {file_to_send} sent to receiver.')
    f.close()
    # Exit! Make sure the receiver ends before the sender. send_end will stop the emulator.
    time.sleep(1.5)
    send_monitor.send_end(receiver_id)