#!/usr/bin/env python3
import socket, time, json, threading

HOST, PORT = 'localhost', 5002

class FixedSenderCase3:
    def __init__(self):
        self.sock = None
        self.interval = 0.1        # seconds (100 ms)
        self.budget  = 4096         # bytes per interval (updated by RX)
        self.cwnd    = 4096         # app-level window to avoid spikes
        self.chunk   = 512          # send chunk size
        self.running = True

    def ctrl_listener(self):
        buf = b""
        while self.running and self.sock:
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
                    if msg.get("type") == "bw":
                        self.budget = int(msg.get("budget", self.budget))
                        self.interval = int(msg.get("interval_ms", int(self.interval*1000))) / 1000.0
                        # Keep cwnd within 2x budget to smooth bursts
                        self.cwnd = min(max(self.cwnd, self.budget), self.budget * 2)
                except:
                    pass

    def run(self, seconds=12):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        print(f"[TX3] Connected to {HOST}:{PORT}")
        threading.Thread(target=self.ctrl_listener, daemon=True).start()

        end = time.time() + seconds
        while time.time() < end:
            allowed = min(self.budget, self.cwnd)
            sent = 0
            # Shape transmission: spread allowed bytes into small chunks
            while sent < allowed:
                n = min(self.chunk, allowed - sent)
                try:
                    self.sock.sendall(b'Z' * n)
                except Exception as e:
                    print(f"[TX3] send error: {e}")
                    end = 0; break
                sent += n
                # tiny pacing gap to avoid micro-bursts
                time.sleep(0.002)
            print(f"[TX3] interval={int(self.interval*1000)}ms budget={self.budget}B cwnd={self.cwnd}B sent={sent}B")
            # Conservative AIMD adjust
            if sent >= self.budget:
                self.cwnd = max(self.budget, int(self.cwnd * 0.95))
            else:
                self.cwnd = min(self.budget * 2, int(self.cwnd + self.chunk))
            time.sleep(self.interval)

        try: self.sock.close()
        except: pass
        print("[TX3] Done")

if __name__ == "__main__":
    FixedSenderCase3().run()
