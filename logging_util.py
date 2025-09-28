#!/usr/bin/env python3
# File: logging_util.py (CREATE THIS FILE IN PROJECT ROOT)

import time
import threading

class BufferLogger:
    def __init__(self, log_file='buffer_log.txt'):
        self._log_file = log_file
        self._value_to_log = 0
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
    
    def _run(self):
        with open(self._log_file, 'w') as f:
            f.write('Timestamp,BufferSize\n')
            start_time = time.time()
            while not self._stop_event.wait(timeout=1.0):
                elapsed_time = time.time() - start_time
                f.write(f'{elapsed_time},{self._value_to_log}\n')
                f.flush()
    
    def update_buffer_size(self, size):
        self._value_to_log = size
    
    def start(self):
        self._thread.start()
    
    def stop(self):
        self._stop_event.set()
        self._thread.join()