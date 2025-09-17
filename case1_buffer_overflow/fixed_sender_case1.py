#!/usr/bin/env python3
import socket, time, json, threading, sys

HOST, PORT = 'localhost', 5000

class SenderFixed:
    def __init__(self):
        self.rate_delay = 0.01     # start with 10 ms between chunks
        self.chunk_size = 1024      # 1 KB chunks (smaller than before)
        self.ctrl_level = "OK"
        self.sock = None

    def listen_control(self):
        """Read control lines prefixed with #CTRL# and adjust sending."""
        buf = b""
        while self.sock:
            try:
                self.sock.settimeout(0.05)
                data = self.sock.recv(4096)
            except:
                data = b""
            if not data:
                time.sleep(0.02); continue
            buf += data
            while b"#CTRL#" in buf:
                i = buf.find(b"#CTRL#")
                if i > 0:
                    buf = buf[i:]
                nl = buf.find(b"\n")
                if nl == -1: break
                line = buf[len("#CTRL#"):nl].decode(errors="ignore")
                buf = buf[nl+1:]
                try:
                    msg = json.loads(line)
                    if msg.get("type") == "buffer_status":
                        level = msg.get("level","OK")
                        self.ctrl_level = level
                        if level == "SLOW":
                            # increase delay and reduce chunk size
                            self.rate_delay = min(0.05, self.rate_delay + 0.005)
                            self.chunk_size = max(512, self.chunk_size - 128)
                        elif level == "FAST":
                            # cautiously speed up
                            self.rate_delay = max(0.005, self.rate_delay - 0.002)
                            self.chunk_size = min(2048, self.chunk_size + 128)
                except:
                    pass

    def run(self, total_packets=2000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        print(f"[TX] Connected to {HOST}:{PORT}")
        threading.Thread(target=self.listen_control, daemon=True).start()

        sent = 0
        while sent < total_packets:
            payload = ("D"* (self.chunk_size-12)).encode()
            frame = f"PKT{sent:06d}".encode() + payload
            try:
                self.sock.sendall(frame)
                sent += 1
                if sent % 200 == 0:
                    print(f"[TX] sent={sent}, delay={self.rate_delay*1000:.1f}ms, chunk={self.chunk_size}B, ctrl={self.ctrl_level}")
                time.sleep(self.rate_delay)
            except Exception as e:
                print(f"[TX] send error: {e}"); break

        print(f"[TX] done, total sent={sent}")
        try: self.sock.close()
        except: pass

if __name__ == "__main__":
    SenderFixed().run()
