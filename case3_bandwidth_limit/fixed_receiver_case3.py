#!/usr/bin/env python3
import socket, time, json, threading

HOST, PORT = 'localhost', 5002

# Configure bandwidth cap
# Example: 300 kbps ≈ 300_000 bits/s ≈ 37_500 B/s
BW_LIMIT_BPS   = 300_000
INTERVAL_MS    = 100                 # update every 100 ms
BYTES_PER_INT  = (BW_LIMIT_BPS // 8) * INTERVAL_MS // 1000

class FixedReceiverCase3:
    def __init__(self):
        self.conn = None
        self.tokens = BYTES_PER_INT
        self.last_refill = time.time()
        self.running = True

    def refill_and_signal(self):
        """Refill bucket each INTERVAL and tell sender the allowed budget."""
        interval = INTERVAL_MS / 1000.0
        while self.running and self.conn:
            time.sleep(interval)
            self.tokens = BYTES_PER_INT  # reset budget each interval
            msg = {"type": "bw", "budget": BYTES_PER_INT, "interval_ms": INTERVAL_MS}
            try:
                self.conn.sendall(("#CTRL#" + json.dumps(msg) + "\n").encode())
            except:
                break

    def serve(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT)); s.listen(1)
        print(f"[RX3] Fixed receiver on {HOST}:{PORT} cap≈{BW_LIMIT_BPS/1000:.0f} kbps; interval={INTERVAL_MS} ms; budget={BYTES_PER_INT} B")

        self.conn, addr = s.accept()
        print(f"[RX3] Client {addr} connected")

        threading.Thread(target=self.refill_and_signal, daemon=True).start()

        while True:
            try:
                data = self.conn.recv(4096)
                if not data:
                    break
                # Enforce the cap (police): consume budget, drop if over
                if len(data) <= self.tokens:
                    self.tokens -= len(data)
                    # Data accepted (do nothing else; we only emulate a sink)
                else:
                    # Over budget this interval -> drop
                    pass
            except Exception as e:
                print(f"[RX3] recv error: {e}")
                break

        self.running = False
        try: self.conn.close()
        except: pass
        s.close()
        print("[RX3] Closed")

if __name__ == "__main__":
    FixedReceiverCase3().serve()
