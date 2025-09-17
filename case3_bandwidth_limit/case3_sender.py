#!/usr/bin/env python3
import socket
import time
import sys

def start_sender():
    HOST = 'localhost'
    PORT = 5002
    
    high_rate = "--fast" in sys.argv
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    
    print(f"Connected to {HOST}:{PORT}")
    print(f"Mode: {'HIGH RATE' if high_rate else 'NORMAL RATE'}")
    
    packets_sent = 0
    
    if high_rate:
        # Send at high rate to exceed bandwidth
        for i in range(200):
            data = f"FAST_PACKET_{i}_" + "Z" * 800
            sock.send(data.encode())
            packets_sent += 1
            
            if packets_sent % 20 == 0:
                print(f"Sent {packets_sent} packets at high rate")
            
            time.sleep(0.01)  # 10ms delay (high rate)
    else:
        # Normal rate
        for i in range(50):
            data = f"NORMAL_PACKET_{i}_" + "Z" * 800
            sock.send(data.encode())
            packets_sent += 1
            
            if packets_sent % 10 == 0:
                print(f"Sent {packets_sent} packets")
            
            time.sleep(1)  # 1 second delay
    
    print(f"Total packets sent: {packets_sent}")
    sock.close()

if __name__ == "__main__":
    start_sender()
