"""
Simplified log display module.
The main log viewer is now integrated in the LogsTab.
This module provides the LogCapture singleton for backward compatibility.
"""

import sys
import os
import threading
import queue
import io


class TeeStream:
    """File-like object that writes to two streams."""

    def __init__(self, stream1, stream2):
        self.stream1 = stream1
        self.stream2 = stream2

    def write(self, data):
        self.stream1.write(data)
        self.stream2.write(data)
        self.flush()
        return len(data)

    def flush(self):
        try:
            self.stream1.flush()
        except (ValueError, OSError):
            pass
        if hasattr(self.stream2, 'flush'):
            try:
                self.stream2.flush()
            except (ValueError, OSError):
                pass

    def __getattr__(self, attr):
        return getattr(self.stream1, attr)


class LogCapture:
    """
    Captures stdout/stderr into a queue for display.
    Uses a polling thread with a StringIO buffer.
    """

    def __init__(self):
        self.log_queue = queue.Queue()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.capturing = False
        self.stdout_buffer = None
        self.stderr_buffer = None

    def start_capture(self):
        if self.capturing:
            return
        self.capturing = True
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        sys.stdout = TeeStream(self.original_stdout, self.stdout_buffer)
        sys.stderr = TeeStream(self.original_stderr, self.stderr_buffer)
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        self.log_queue.put(("INFO", "=== Début de la capture des logs ==="))

    def _capture_loop(self):
        import time
        while self.capturing:
            try:
                if self.stdout_buffer:
                    self.stdout_buffer.seek(0)
                    data = self.stdout_buffer.read()
                    if data:
                        for line in data.split('\n'):
                            if line.strip():
                                self.log_queue.put(("STDOUT", line))
                        self.stdout_buffer.seek(0)
                        self.stdout_buffer.truncate()
                if self.stderr_buffer:
                    self.stderr_buffer.seek(0)
                    data = self.stderr_buffer.read()
                    if data:
                        for line in data.split('\n'):
                            if line.strip():
                                self.log_queue.put(("STDERR", line))
                        self.stderr_buffer.seek(0)
                        self.stderr_buffer.truncate()
                time.sleep(0.1)
            except Exception as e:
                self.log_queue.put(("ERROR", f"Erreur de capture: {e}"))
                break

    def stop_capture(self):
        self.capturing = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=1)
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.log_queue.put(("INFO", "=== Fin de la capture des logs ==="))

    def get_logs(self):
        logs = []
        while not self.log_queue.empty():
            try:
                source, message = self.log_queue.get_nowait()
                logs.append(f"[{source}] {message}")
            except queue.Empty:
                break
        return '\n'.join(logs)


# Singleton
_log_capture = None


def get_log_capture():
    global _log_capture
    if _log_capture is None:
        _log_capture = LogCapture()
    return _log_capture


def start_log_capture():
    capture = get_log_capture()
    capture.start_capture()
    return capture


def stop_log_capture():
    capture = get_log_capture()
    if capture:
        capture.stop_capture()


def log_message(message, level="INFO"):
    capture = get_log_capture()
    if capture:
        capture.log_queue.put((level, message))