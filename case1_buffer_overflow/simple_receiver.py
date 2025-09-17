#!/usr/bin/env python3
import socket
import time
import sys

def start_receiver():
    HOST = 'localhost'
    PORT = 5000
    BUFFER_LIMIT = 1024 * 10  # 10KB buffer (very small to force overflow)
    
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
            
            # Slowly process buffer
            time.sleep(0.1)
            current_buffer = max(0, current_buffer - 100)
            
        except KeyboardInterrupt:
            break
    
    print(f"\nFinal Stats: Received={packets_received}, Dropped={packets_dropped}")
    conn.close()
    sock.close()

if __name__ == "__main__":
    start_receiver()
