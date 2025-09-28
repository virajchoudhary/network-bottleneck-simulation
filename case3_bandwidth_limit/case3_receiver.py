#!/usr/bin/env python3
# File: case3_bandwidth_limit/case3_receiver.py (REPLACE YOUR EXISTING FILE)

import socket
import time
from logging_util import BufferLogger  # NEW LINE ADDED

def start_receiver():
    logger = BufferLogger('case3_bandwidth_limit/bandwidth_log.txt')  # NEW LINE ADDED
    logger.start()  # NEW LINE ADDED
    
    HOST = 'localhost'
    PORT = 5002
    BANDWIDTH_LIMIT = 1024 * 10  # 10KB/sec limit (very low)
    
    try:  # NEW TRY BLOCK ADDED
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(1)
        
        print(f"Bandwidth Limited Receiver listening on {HOST}:{PORT}")
        print(f"Bandwidth limit: {BANDWIDTH_LIMIT} bytes/sec")
        
        packets_received = 0
        packets_dropped = 0
        bytes_received = 0
        start_time = time.time()
        last_log_time = start_time
        bytes_this_second = 0
        
        conn, addr = sock.accept()
        print(f"Connected to {addr}")
        
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                
                current_time = time.time()
                elapsed = current_time - start_time
                current_rate = bytes_received / elapsed if elapsed > 0 else 0
                
                # Track bytes per second for logging
                if current_time - last_log_time >= 1.0:
                    logger.update_buffer_size(bytes_this_second)  # NEW LINE ADDED
                    bytes_this_second = 0
                    last_log_time = current_time
                else:
                    bytes_this_second += len(data)
                
                # Drop packets if exceeding bandwidth
                if current_rate > BANDWIDTH_LIMIT:
                    packets_dropped += 1
                    print(f"BANDWIDTH EXCEEDED! Dropped packet {packets_dropped}")
                else:
                    packets_received += 1
                    bytes_received += len(data)
                    
                    if packets_received % 10 == 0:
                        print(f"Received: {packets_received}, Rate: {current_rate:.0f} B/s")
                
            except KeyboardInterrupt:
                break
        
        print(f"\nStats: Received={packets_received}, Dropped={packets_dropped}")
        conn.close()
        sock.close()
        
    finally:  # NEW FINALLY BLOCK ADDED
        logger.stop()  # NEW LINE ADDED

if __name__ == "__main__":
    start_receiver()