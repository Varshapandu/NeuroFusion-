# # backend/services/supernode_client.py
# import requests
# import socket
# import time
#
# FL_BACKEND = "http://127.0.0.1:5000"
#
# def heartbeat_loop():
#     node_id = socket.gethostname()
#     while True:
#         try:
#             requests.post(
#                 f"{FL_BACKEND}/api/fl/node_heartbeat",
#                 json={
#                     "node_id": node_id,
#                     "status": "online"
#                 },
#                 timeout=2
#             )
#         except Exception as e:
#             print("[HEARTBEAT ERROR]", e)
#         time.sleep(5)
#
# import threading
# import logging
# import sys
# import socket
# import time
# import requests
# import psutil
# from typing import Dict, Any
#
# from backend.services.logs_service import emit_log
#
# # Import Flower training client
# try:
#     from federated.supernode_client import start_client_main
# except Exception as e:
#     raise RuntimeError(f"Cannot import training client: {e}")
#
# # -------------------------------------------------------------
# # GLOBAL STATE
# # -------------------------------------------------------------
# _client_thread = None
# _client_running = False
# _stop_flag = False
#
# HEARTBEAT_URL = "http://127.0.0.1:5000/api/fl/node_heartbeat"
#
#
# logger = logging.getLogger("backend.supernode_client")
# logger.setLevel(logging.INFO)
# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
# logger.addHandler(handler)
#
#
# import requests
#
# def send_heartbeat(node_id, status="online", rounds_completed=None):
#     try:
#         requests.post(
#             "http://127.0.0.1:5000/api/fl/node_heartbeat",
#             json={
#                 "node_id": node_id,
#                 "status": status,
#                 "rounds_completed": rounds_completed,
#             },
#             timeout=2,
#         )
#     except Exception as e:
#         print(f"[HB] Failed to send heartbeat: {e}")
#
#
# # -------------------------------------------------------------
# # HARDWARE INFO
# # -------------------------------------------------------------
# def get_hardware_info():
#     gpu = "Unknown"
#     try:
#         import torch
#         gpu = "CUDA" if torch.cuda.is_available() else "None"
#     except:
#         pass
#     try:
#         return {
#             "cpu": f"{psutil.cpu_count(logical=True)} cores",
#             "ram": f"{round(psutil.virtual_memory().total / (1024**3), 1)} GB",
#             "gpu": gpu,
#         }
#     except:
#         return {"cpu": "unknown", "ram": "unknown", "gpu": gpu}
#
#
# # -------------------------------------------------------------
# # HEARTBEAT THREAD
# # -------------------------------------------------------------
# def heartbeat_loop(node_id):
#     """Send heartbeat every 5 seconds."""
#     while not _stop_flag:
#         try:
#             ip = socket.gethostbyname(socket.gethostname())
#             payload = {
#                 "node_id": node_id,
#                 "ip": ip,
#                 "status": "online",
#                 "meta": get_hardware_info(),
#             }
#             requests.post(HEARTBEAT_URL, json=payload, timeout=2)
#
#         except Exception as e:
#             emit_log(f"[HEARTBEAT ERROR] {e}")
#
#         time.sleep(5)
#
#
# # -------------------------------------------------------------
# # LOG INTERCEPTOR (stdout + stderr)
# # -------------------------------------------------------------
# class LogInterceptor:
#     """Redirect Flower logs into dashboard via emit_log()."""
#     def write(self, message):
#         message = message.strip()
#         if message:
#             emit_log(f"[CLIENT] {message}")
#
#     def flush(self):
#         pass
#
#
# class ErrorInterceptor:
#     """Redirect stderr."""
#     def write(self, message):
#         message = message.strip()
#         if message:
#             emit_log(f"[CLIENT-ERR] {message}")
#
#     def flush(self):
#         pass
#
#
# # -------------------------------------------------------------
# # MAIN CLIENT LAUNCHER
# # -------------------------------------------------------------
# def launch_fl_client(server_address: str = None) -> Dict[str, Any]:
#     """
#     Safely start a federated learning client in a background thread.
#     Includes:
#         - log streaming
#         - heartbeat
#         - crash handling
#         - TRAINING → IDLE transitions
#     """
#     global _client_thread, _client_running, _stop_flag
#
#     if _client_running:
#         msg = "FL client already running"
#         emit_log(f"[WARNING] {msg}")
#         return {"status": "already_running", "message": msg}
#
#     _stop_flag = False
#     node_id = socket.gethostname()
#     # ---------------------------------------------------------
#     # REGISTER NODE IMMEDIATELY (dashboard visibility fix)
#     # ---------------------------------------------------------
#     from backend.routes.fl_routes import _update_node_from_ping
#
#     try:
#         ip = socket.gethostbyname(socket.gethostname())
#     except Exception:
#         ip = "127.0.0.1"
#
#     _update_node_from_ping(
#         node_id=node_id,
#         ip=socket.gethostbyname(socket.gethostname()),
#         status="idle",
#         meta=get_hardware_info()
#     )
#
#     emit_log(f"[INFO] Node {node_id} registered with dashboard")
#
#     # ---------------------------------------------------------
#     # HEARTBEAT thread
#     # ---------------------------------------------------------
#     threading.Thread(
#         target=heartbeat_loop,
#         args=(node_id,),
#         daemon=True,
#     ).start()
#
#     emit_log(f"[INFO] Heartbeat started for node {node_id}")
#
#     # ---------------------------------------------------------
#     # Worker: run the actual Flower client
#     # ---------------------------------------------------------
#     def _worker():
#         global _client_running
#         _client_running = True
#
#         # Redirect logs
#         sys.stdout = LogInterceptor()
#         sys.stderr = ErrorInterceptor()
#
#         # Mark as TRAINING
#         # Mark as CONNECTED / IDLE
#         try:
#             from backend.routes.fl_routes import _update_node_from_ping
#             _update_node_from_ping(node_id, status="idle")
#         except:
#             pass
#
#         emit_log(f"[CLIENT] Node {node_id} → CONNECTED / WAITING")
#
#
#         try:
#             if server_address:
#                 emit_log(f"[CLIENT] Connecting to FL server: {server_address}")
#                 start_client_main(server_address=server_address)
#             else:
#                 emit_log("[CLIENT] Starting FL client with default server")
#                 start_client_main()
#
#             emit_log("[CLIENT] Training finished successfully")
#
#         except Exception as e:
#             emit_log(f"[CLIENT ERROR] Crash: {e}")
#
#         finally:
#             # Mark IDLE
#             try:
#                 from backend.routes.fl_routes import _update_node_from_ping
#                 _update_node_from_ping(node_id, status="idle")
#             except:
#                 pass
#
#             emit_log(f"[CLIENT] Node {node_id} → IDLE")
#             _client_running = False
#
#     # ---------------------------------------------------------
#     # Start client thread
#     # ---------------------------------------------------------
#     _client_thread = threading.Thread(target=_worker, daemon=True, name="fl-client-thread")
#     _client_thread.start()
#
#     emit_log("[INFO] Federated client started")
#
#     return {"status": "started", "thread_name": "fl-client-thread"}
#
#
# # -------------------------------------------------------------
# # OPTIONAL: STOP CLIENT (future use)
# # -------------------------------------------------------------
# def stop_fl_client():
#     """Not used yet but ready for future STOP API."""
#     global _stop_flag
#     _stop_flag = True
#     emit_log("[INFO] Stop signal sent to FL client")
# # -------------------------------------------------------------
# # RUN AS STANDALONE SCRIPT
# # -------------------------------------------------------------
# if __name__ == "__main__":
#     print("🚀 Starting Local Federated Client Wrapper...")
#
#     # Start the federated client
#     result = launch_fl_client(server_address="127.0.0.1:8080")
#     print(result)
#
#     # Keep the main thread alive so logs + heartbeat stay active
#     while True:
#         time.sleep(1)
#

# backend/services/supernode_client.py
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
sys.path.insert(0, PROJECT_ROOT)


import sys
import time
import socket
import threading
import logging
from typing import Dict, Any

import requests
import psutil

from backend.services.logs_service import emit_log

# Import Flower training client
try:
    from federated.supernode_client import start_client_main
except Exception as e:
    raise RuntimeError(f"Cannot import training client: {e}")

# -------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------
HEARTBEAT_URL = "http://127.0.0.1:5000/api/fl/node_heartbeat"
HEARTBEAT_INTERVAL = 5  # seconds

# -------------------------------------------------------------
# GLOBAL STATE
# -------------------------------------------------------------
_client_thread = None
_client_running = False
_stop_flag = False

# -------------------------------------------------------------
# LOGGER
# -------------------------------------------------------------
logger = logging.getLogger("backend.supernode_client")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
logger.addHandler(handler)

# -------------------------------------------------------------
# HARDWARE INFO
# -------------------------------------------------------------
def get_hardware_info():
    gpu = "Unknown"
    try:
        import torch
        gpu = "CUDA" if torch.cuda.is_available() else "None"
    except:
        pass

    try:
        return {
            "cpu": f"{psutil.cpu_count(logical=True)} cores",
            "ram": f"{round(psutil.virtual_memory().total / (1024**3), 1)} GB",
            "gpu": gpu,
        }
    except:
        return {"cpu": "unknown", "ram": "unknown", "gpu": gpu}

# -------------------------------------------------------------
# HEARTBEAT THREAD
# -------------------------------------------------------------
def heartbeat_loop(node_id: str):
    """Send heartbeat to backend every few seconds."""
    while not _stop_flag:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            payload = {
                "node_id": node_id,
                "ip": ip,
                "status": "online",
                "meta": get_hardware_info(),
            }
            requests.post(HEARTBEAT_URL, json=payload, timeout=2)
        except Exception as e:
            emit_log(f"[HEARTBEAT ERROR] {e}")

        time.sleep(HEARTBEAT_INTERVAL)

# -------------------------------------------------------------
# LOG INTERCEPTORS
# -------------------------------------------------------------
class LogInterceptor:
    def write(self, message):
        message = message.strip()
        if message:
            emit_log(f"[CLIENT] {message}")

    def flush(self):
        pass

class ErrorInterceptor:
    def write(self, message):
        message = message.strip()
        if message:
            emit_log(f"[CLIENT-ERR] {message}")

    def flush(self):
        pass

# -------------------------------------------------------------
# MAIN CLIENT LAUNCHER
# -------------------------------------------------------------
def launch_fl_client(server_address: str = None) -> Dict[str, Any]:
    """
    Start federated learning client safely in background.
    Includes:
      - heartbeat
      - log streaming
      - correct node state transitions
    """
    global _client_thread, _client_running, _stop_flag

    if _client_running:
        msg = "FL client already running"
        emit_log(f"[WARNING] {msg}")
        return {"status": "already_running", "message": msg}

    _stop_flag = False
    node_id = socket.gethostname()

    emit_log(f"[INFO] Starting FL client on node: {node_id}")

    # ---------------------------------------------------------
    # INITIAL REGISTRATION (via heartbeat)
    # ---------------------------------------------------------
    try:
        ip = socket.gethostbyname(socket.gethostname())
        requests.post(
            HEARTBEAT_URL,
            json={
                "node_id": node_id,
                "ip": ip,
                "status": "idle",
                "meta": get_hardware_info(),
            },
            timeout=2,
        )
    except Exception as e:
        emit_log(f"[REGISTER ERROR] {e}")

    # ---------------------------------------------------------
    # HEARTBEAT THREAD
    # ---------------------------------------------------------
    threading.Thread(
        target=heartbeat_loop,
        args=(node_id,),
        daemon=True,
        name="heartbeat-thread",
    ).start()

    emit_log(f"[INFO] Heartbeat started for node {node_id}")

    # ---------------------------------------------------------
    # WORKER THREAD (Flower client)
    # ---------------------------------------------------------
    def _worker():
        global _client_running
        _client_running = True

        # Redirect logs
        sys.stdout = LogInterceptor()
        sys.stderr = ErrorInterceptor()

        # Mark TRAINING
        try:
            requests.post(
                HEARTBEAT_URL,
                json={"node_id": node_id, "status": "training"},
                timeout=2,
            )
            emit_log(f"[CLIENT] Node {node_id} → TRAINING")
        except:
            pass

        try:
            if server_address:
                emit_log(f"[CLIENT] Connecting to FL server at {server_address}")
                start_client_main(server_address=server_address)
            else:
                emit_log("[CLIENT] Starting FL client (default server)")
                start_client_main()

            emit_log("[CLIENT] Training finished successfully")

        except Exception as e:
            emit_log(f"[CLIENT ERROR] {e}")

        finally:
            # Mark IDLE
            try:
                requests.post(
                    HEARTBEAT_URL,
                    json={"node_id": node_id, "status": "idle"},
                    timeout=2,
                )
                emit_log(f"[CLIENT] Node {node_id} → IDLE")
            except:
                pass

            _client_running = False

    # ---------------------------------------------------------
    # START CLIENT THREAD
    # ---------------------------------------------------------
    _client_thread = threading.Thread(
        target=_worker,
        daemon=True,
        name="fl-client-thread",
    )
    _client_thread.start()

    emit_log("[INFO] Federated client started")

    return {"status": "started", "node_id": node_id}

# -------------------------------------------------------------
# OPTIONAL STOP (future use)
# -------------------------------------------------------------
def stop_fl_client():
    global _stop_flag
    _stop_flag = True
    emit_log("[INFO] Stop signal sent to FL client")

# -------------------------------------------------------------
# STANDALONE RUN
# -------------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting Local Federated Client Wrapper...")
    result = launch_fl_client(server_address="127.0.0.1:8080")
    print(result)
    while True:
        time.sleep(1)
