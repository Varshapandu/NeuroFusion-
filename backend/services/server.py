# backend/services/server.py

import threading
import sys
import time
from backend.services.logs_service import emit_log
_server_running = False

# Import your actual Flower server launcher
from federated.server import start_fl_server


# -------------------------------------------------------------------
# Custom log interceptor to capture Flower server logs in real-time
# -------------------------------------------------------------------
class LogInterceptor:
    def write(self, message):
        message = message.strip()
        if message:
            emit_log(f"[SERVER] {message}")
    def flush(self):
        pass


# -------------------------------------------------------------------
# Background server launcher (used by Flask)
# -------------------------------------------------------------------
def launch_fl_server():
    global _server_running

    if _server_running:
        emit_log("[SERVER] Flower server already running")
        return {"status": "already_running"}

    _server_running = True

    def run_server():
        import sys
        from backend.services.logs_service import emit_log
        from federated.server import start_fl_server

        emit_log("[SERVER] Federated Server: Starting…")
        start_fl_server()

    import threading
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    return {"status": "started"}


# -------------------------------------------------------------------
# DIRECT CLI MODE — when you run:
#   python -m backend.services.server
# -------------------------------------------------------------------
def start_server():
    """Run FL server directly without Flask."""
    print("[FL SERVER] Starting server...")

    # Do NOT redirect stdout here, only inside launch_fl_server()
    try:
        start_fl_server()
    except Exception as e:
        print(f"[FL SERVER ERROR] {e}")


if __name__ == "__main__":
    start_server()

