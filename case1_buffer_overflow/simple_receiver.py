#!/usr/bin/env python3
# File: case1_buffer_overflow/simple_receiver.py (REPLACE YOUR EXISTING FILE)

import socket
import time
import sys
from logging_util import BufferLogger  # NEW LINE ADDED

def start_receiver():
    logger = BufferLogger('case1_buffer_overflow/buffer_log.txt')  # NEW LINE ADDED
    logger.start()  # NEW LINE ADDED
    
    HOST = 'localhost'
    PORT = 5000
    BUFFER_LIMIT = 1024 * 10  # 10KB buffer (very small to force overflow)
    
    try:  # NEW TRY BLOCK ADDED
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(1)
        
        print(f"Buffer Overflow Receiver listening on {HOST}:{PORT}")
        print(f"Buffer limit: {BUFFER_LIMIT} bytes")
        
        packets_received = 0
        packets_dropped = 0
        current_buffer = 0
        
        conn, addr = sock.accept()
        print(f"Connected to {addr}")
        
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                    
                # Check buffer overflow
                if current_buffer + len(data) > BUFFER_LIMIT:
                    packets_dropped += 1
                    print(f"BUFFER OVERFLOW! Dropped packet {packets_dropped}")
                else:
                    packets_received += 1
                    current_buffer += len(data)
                    if packets_received % 10 == 0:
                        print(f"Received: {packets_received}, Buffer: {current_buffer}/{BUFFER_LIMIT}")
                
                # Log current buffer size for analysis
                logger.update_buffer_size(current_buffer)  # NEW LINE ADDED
                
                # Slowly process buffer
                time.sleep(0.1)
                current_buffer = max(0, current_buffer - 100)
                
            except KeyboardInterrupt:
                break
        
        print(f"\nFinal Stats: Received={packets_received}, Dropped={packets_dropped}")
        conn.close()
        sock.close()
    
    finally:  # NEW FINALLY BLOCK ADDED
        logger.stop()  # NEW LINE ADDED

if __name__ == "__main__":
    start_receiver()
