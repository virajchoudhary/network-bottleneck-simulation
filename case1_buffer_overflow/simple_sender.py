#!/usr/bin/env python3
import socket
import time
import sys

def start_sender():
    HOST = 'localhost'
    PORT = 5000
    
    # Check for overload mode
    overload = "--overload" in sys.argv
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    
    print(f"Connected to {HOST}:{PORT}")
    print(f"Mode: {'OVERLOAD' if overload else 'NORMAL'}")
    
    packets_sent = 0
    
    if overload:
        # Send 1000 packets quickly to cause overflow
        for i in range(1000):
            data = f"PACKET_{i}_" + "X" * 500
            sock.send(data.encode())
            packets_sent += 1
            
            if packets_sent % 100 == 0:
                print(f"Sent {packets_sent} packets")
            
            time.sleep(0.01)  # Very fast sending
    else:
        # Normal mode - slower sending
        for i in range(100):
            data = f"PACKET_{i}_" + "X" * 500
            sock.send(data.encode())
            packets_sent += 1
            
            if packets_sent % 10 == 0:
                print(f"Sent {packets_sent} packets")
            
            time.sleep(0.5)  # Half second delay
    
    print(f"Total packets sent: {packets_sent}")
    sock.close()

if __name__ == "__main__":
    start_sender()
