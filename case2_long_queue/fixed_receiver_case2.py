#!/usr/bin/env python3

import socket, time, threading, queue, json, random
from logging_util import BufferLogger  # NEW LINE ADDED

HOST, PORT = 'localhost', 5001

# Queue and RED thresholds (tune here)
Q_MAX = 800                 # hard cap
Q_MIN_TH = 250              # RED min threshold
Q_MAX_TH = 600              # RED max threshold
WORKERS = 6                 # more workers to drain faster
PROC_DELAY_SEC = 0.01       # per-item processing time

class FixedReceiverCase2:
    def __init__(self):
        self.q = queue.Queue(maxsize=Q_MAX)
        self.conn = None
        self.running = True
        self.logger = BufferLogger('case2_long_queue/queue_log.txt')  # NEW LINE ADDED

    def worker(self, wid):
        while self.running:
            try:
                data = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            # Simulate work
            time.sleep(PROC_DELAY_SEC)
            self.q.task_done()

    def red_drop(self):
        ql = self.q.qsize()
        if ql <= Q_MIN_TH:   # accept
            return False
        if ql >= Q_MAX_TH:   # drop aggressively
            return True
        # Linear probability between thresholds
        p = (ql - Q_MIN_TH) / float(Q_MAX_TH - Q_MIN_TH)
        return random.random() < p

    def control_sender(self):
        while self.running and self.conn:
            ql = self.q.qsize()
            # 3-level feedback for sender
            if ql >= Q_MAX_TH:
                level = "SLOW"
            elif ql <= Q_MIN_TH // 2:
                level = "FAST"
            else:
                level = "OK"
            msg = {"type":"queue","qlen":ql,"level":level}
            try:
                self.conn.sendall(("#CTRL#" + json.dumps(msg) + "\n").encode())
            except:
                break
            time.sleep(0.2)

    def serve(self):
        self.logger.start()  # NEW LINE ADDED
        try:  # NEW TRY BLOCK ADDED
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT)); s.listen(1)
            print(f"[RX2] Fixed receiver on {HOST}:{PORT} Qmax={Q_MAX}, workers={WORKERS}")
            self.conn, addr = s.accept()
            print(f"[RX2] Client {addr} connected")

            # Start workers and control loop
            for i in range(WORKERS):
                threading.Thread(target=self.worker, args=(i,), daemon=True).start()
            threading.Thread(target=self.control_sender, daemon=True).start()

            while True:
                try:
                    data = self.conn.recv(4096)
                    if not data:
                        break
                    # RED/tail-drop
                    if self.red_drop():
                        continue
                    try:
                        self.q.put_nowait(data)
                    except queue.Full:
                        # Hard tail drop
                        pass
                    
                    # Log current queue size for analysis
                    self.logger.update_buffer_size(self.q.qsize())  # NEW LINE ADDED
                    
                except Exception as e:
                    print(f"[RX2] recv error: {e}")
                    break

            self.running = False
            try: self.conn.close()
            except: pass
            s.close()
            print("[RX2] Closed")
            
        finally:  # NEW  BLOCK ADDED
            self.logger.stop()  # NEW LINE ADDED

if __name__ == "__main__":
    FixedReceiverCase2().serve()