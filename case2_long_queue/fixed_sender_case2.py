#!/usr/bin/env python3
import socket, time, json, threading, statistics

HOST, PORT = 'localhost', 5001

class FixedSenderCase2:
    def __init__(self):
        # Pacing knobs
        self.batch = 12              # items per cycle (small bursts)
        self.delay = 0.012           # delay between cycles (12 ms)
        self.min_delay = 0.004
        self.max_delay = 0.05
        self.min_batch = 4
        self.max_batch = 24

        # RTT trend estimate (optional)
        self.rtt = []
        self.sock = None
        self.level = "OK"

    def listen_control(self):
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
                    if msg.get("type") == "queue":
                        self.level = msg.get("level","OK")
                        # Queue-aware pacing adjustments
                        if self.level == "SLOW":
                            self.delay = min(self.max_delay, self.delay + 0.004)
                            self.batch = max(self.min_batch, self.batch - 2)
                        elif self.level == "FAST":
                            self.delay = max(self.min_delay, self.delay - 0.003)
                            self.batch = min(self.max_batch, self.batch + 1)
                        else:
                            # gentle AIMD toward stability
                            self.delay = min(self.max_delay, self.delay + 0.001)
                except:
                    pass

    def run(self, seconds=12):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        print(f"[TX2] Connected to {HOST}:{PORT}")
        threading.Thread(target=self.listen_control, daemon=True).start()

        t_end = time.time() + seconds
        sent = 0
        while time.time() < t_end:
            t_cycle_start = time.time()
            # Send small records to reduce queue spikes
            for _ in range(self.batch):
                payload = f"{time.time():.6f}".encode() + b"|" + b"A"*512
                t0 = time.time()
                try:
                    self.sock.sendall(payload)
                except Exception as e:
                    print(f"[TX2] send error: {e}")
                    t_end = 0; break
                t1 = time.time()
                self.rtt.append(t1 - t0)
                sent += 1

            # RTT trend guard: if recent average rises, slow a bit
            if len(self.rtt) >= 40:
                avg = statistics.mean(self.rtt[-40:])
                if avg > 0.025:
                    self.delay = min(self.max_delay, self.delay + 0.003)
                elif avg < 0.010:
                    self.delay = max(self.min_delay, self.delay - 0.001)

            elapsed = time.time() - t_cycle_start
            sleep_for = max(0.0, self.delay - elapsed)
            print(f"[TX2] level={self.level} batch={self.batch} delay={self.delay*1000:.1f}ms sent={sent}")
            time.sleep(sleep_for)

        try: self.sock.close()
        except: pass
        print(f"[TX2] done, sent={sent}")

if __name__ == "__main__":
    FixedSenderCase2().run()
