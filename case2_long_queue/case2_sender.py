#!/usr/bin/env python3
import socket
import time
import sys

def start_sender():
    HOST = 'localhost'
    PORT = 5001
    
    burst_mode = "--burst" in sys.argv
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    
    print(f"Connected to {HOST}:{PORT}")
    print(f"Mode: {'BURST' if burst_mode else 'NORMAL'}")
    
    packets_sent = 0
    
    if burst_mode:
        # Send bursts to create queue buildup
        for burst in range(5):
            print(f"Sending burst {burst + 1}")
            for i in range(20):
                data = f"BURST_{burst}_PACKET_{i}_" + "Y" * 300
                sock.send(data.encode())
                packets_sent += 1
                time.sleep(0.02)  # Fast within burst
            
            print(f"Burst {burst + 1} sent, pausing...")
            time.sleep(1)  # Pause between bursts
    else:
        # Normal steady sending
        for i in range(50):
            data = f"NORMAL_PACKET_{i}_" + "Y" * 300
            sock.send(data.encode())
            packets_sent += 1
            
            if packets_sent % 10 == 0:
                print(f"Sent {packets_sent} packets")
            
            time.sleep(0.3)
    
    print(f"Total packets sent: {packets_sent}")
    sock.close()

if __name__ == "__main__":
    start_sender()
