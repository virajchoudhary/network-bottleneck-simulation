#!/usr/bin/env python3
# File: case1_buffer_overflow/fixed_receiver_case1.py (REPLACE YOUR EXISTING FILE)

import socket, time, threading, json
from logging_util import BufferLogger  # NEW LINE ADDED

HOST, PORT = 'localhost', 5000
APP_BUFFER_LIMIT = 1024 * 200  # 200 KB (was tiny before)
LOW_WATERMARK = int(APP_BUFFER_LIMIT * 0.5)
HIGH_WATERMARK = int(APP_BUFFER_LIMIT * 0.9)

class ReceiverFixed:
    def __init__(self):
        self.app_buffer = 0
        self.conn = None
        self.lock = threading.Lock()
        self.logger = BufferLogger('case1_buffer_overflow/buffer_log.txt')  # NEW LINE ADDED

    def control_sender(self):
        """Periodically send buffer status as control messages."""
        while self.conn:
            with self.lock:
                level = "OK"
                if self.app_buffer >= HIGH_WATERMARK:
                    level = "SLOW"   # ask sender to slow down
                elif self.app_buffer <= LOW_WATERMARK:
                    level = "FAST"   # sender can speed up (within reason)
                msg = {"type":"buffer_status","buffer":self.app_buffer,"level":level}
            try:
                self.conn.sendall(("#CTRL#" + json.dumps(msg) + "\n").encode())
            except:
                break
            time.sleep(0.2)

    def process(self):
        """Drain app buffer steadily."""
        while self.conn:
            with self.lock:
                drain = min(4096, self.app_buffer)  # drain 4 KB per tick
                self.app_buffer -= drain
            time.sleep(0.01)

    def serve(self):
        self.logger.start()  # NEW LINE ADDED
        try:  # NEW TRY BLOCK ADDED
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT)); s.listen(1)
            print(f"[RX] Fixed receiver on {HOST}:{PORT} (buffer={APP_BUFFER_LIMIT}B)")
            self.conn, addr = s.accept()
            print(f"[RX] Client {addr} connected")

            threading.Thread(target=self.process, daemon=True).start()
            threading.Thread(target=self.control_sender, daemon=True).start()

            buf = b""
            while True:
                try:
                    data = self.conn.recv(8192)
                    if not data: break
                    buf += data
                    # Strip control lines from data buffer (sender never embeds "#CTRL#" in data)
                    while b"#CTRL#" in buf:
                        i = buf.find(b"#CTRL#")
                        if i > 0:
                            # count preceding app-data bytes into buffer
                            with self.lock:
                                self.app_buffer += i
                            buf = buf[i:]
                        # remove control line
                        nl = buf.find(b"\n")
                        if nl == -1: break
                        ctrl_line = buf[:nl+1]
                        buf = buf[nl+1:]
                    # Remaining pure app data
                    if buf:
                        with self.lock:
                            self.app_buffer += len(buf)
                        buf = b""
                    
                    # Log current buffer size for analysis
                    with self.lock:
                        self.logger.update_buffer_size(self.app_buffer)  # NEW LINE ADDED
                        
                except Exception as e:
                    print(f"[RX] Error: {e}"); break

            print("[RX] Closing")
            try: self.conn.close()
            except: pass
            s.close()
            
        finally:  # NEW FINALLY BLOCK ADDED
            self.logger.stop()  # NEW LINE ADDED

if __name__ == "__main__":
    ReceiverFixed().serve()