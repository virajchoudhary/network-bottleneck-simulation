#!/usr/bin/env python3
import socket
import time
import threading
from queue import Queue

def start_receiver():
    HOST = 'localhost'
    PORT = 5001
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(1)
    
    print(f"Long Queue Receiver listening on {HOST}:{PORT}")
    
    packet_queue = Queue()
    packets_received = 0
    packets_processed = 0
    
    def process_queue():
        nonlocal packets_processed
        while True:
            if not packet_queue.empty():
                data = packet_queue.get()
                time.sleep(0.2)  # Slow processing (200ms per packet)
                packets_processed += 1
                if packets_processed % 5 == 0:
                    print(f"Processed: {packets_processed}, Queue size: {packet_queue.qsize()}")
            else:
                time.sleep(0.1)
    
    # Start processing thread
    threading.Thread(target=process_queue, daemon=True).start()
    
    conn, addr = sock.accept()
    print(f"Connected to {addr}")
    
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break
            
            packets_received += 1
            packet_queue.put(data)
            
            if packets_received % 10 == 0:
                print(f"Received: {packets_received}, Queue: {packet_queue.qsize()}")
            
            if packet_queue.qsize() > 20:
                print("WARNING: Long queue detected!")
                
        except KeyboardInterrupt:
            break
    
    conn.close()
    sock.close()

if __name__ == "__main__":
    start_receiver()
