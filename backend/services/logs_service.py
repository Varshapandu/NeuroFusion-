import time
import threading
import os

_socketio = None

LOG_DIR = os.path.join(os.getcwd(), "backend", "logs")
LOG_FILE = os.path.join(LOG_DIR, "runtime.log")

# Ensure folder exists
os.makedirs(LOG_DIR, exist_ok=True)

def set_socketio(sio):
    global _socketio
    _socketio = sio


def write_to_file(message):
    """Append log message to runtime.log with timestamp."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} {message}\n")


def emit_log(message, namespace="/logs"):
    """Send a live WS log AND save to file."""
    # Save to file
    write_to_file(message)

    # Emit via WebSocket
    if _socketio:
        try:
            _socketio.emit("log", message, namespace=namespace)
        except Exception:
            pass


def start_background_log_stream(interval_seconds=2, namespace="/logs"):
    """Optional heartbeat logs."""
    def run():
        count = 0
        while True:
            count += 1
            msg = f"[INFO] background heartbeat {count}"
            emit_log(msg, namespace)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
