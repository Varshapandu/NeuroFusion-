# # backend/routes/fl_routes.py
# import os
# import sys
# import time
# import random
# import threading
# from flask import Blueprint, request, jsonify
# from backend.services.logs_service import emit_log
# from backend.extensions import socketio
# import json
# STATE_FILE = "fl_state.json"
#
# # -----------------------------
# # PATH FIX
# # -----------------------------
# CURRENT_DIR = os.path.dirname(__file__)
# PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
# sys.path.insert(0, PROJECT_ROOT)
#
# # -----------------------------
# # SERVICE IMPORTS
# # -----------------------------
# from backend.services.server import launch_fl_server
# from backend.services.supernode_client import launch_fl_client
#
# # -----------------------------
# # BLUEPRINT
# # -----------------------------
# fl_bp = Blueprint("fl", __name__)
#
# # -----------------------------
# # SHARED FL STATE
# # -----------------------------
# FL_STATE = {
#     "nodes": {},
#     "global_round": 0,
#     "current_round": None,
#     "round_running": False,
#     "last_aggregation": None,
#     "metrics": {},
#     "metrics_history": [],
#     "training_progress": {
#         "current": 0,
#         "total": 0
#     }
# }
# STATE_FILE = "fl_state.json"
#
#
# def save_state():
#     try:
#         with open(STATE_FILE, "w") as f:
#             json.dump(FL_STATE, f)
#     except Exception as e:
#         print("[STATE SAVE ERROR]", e)
#
#
# def load_state():
#     global FL_STATE
#     try:
#         if os.path.exists(STATE_FILE):
#             with open(STATE_FILE, "r") as f:
#                 FL_STATE.update(json.load(f))
#             print("[STATE] Restored FL_STATE from disk")
#     except Exception as e:
#         print("[STATE LOAD ERROR]", e)
#
# load_state()
#
#
# _FL_LOCK = threading.Lock()
# NODE_OFFLINE_THRESHOLD = 120  # seconds
#
#
# # -----------------------------
# # Helpers
# # -----------------------------
# def _mark_offline_nodes():
#     """Mark nodes offline if they stop sending heartbeats."""
#     now = time.time()
#     with _FL_LOCK:
#         for nid, info in FL_STATE["nodes"].items():
#             last = info.get("last_seen", 0)
#             if now - last > NODE_OFFLINE_THRESHOLD:
#                 if info.get("status") != "offline":
#                     info["status"] = "offline"
#                     emit_log(f"[{time.strftime('%H:%M:%S')}] Node {nid} marked offline")
#             else:
#                 if info.get("status") == "offline":
#                     info["status"] = "idle"
#                     emit_log(f"[{time.strftime('%H:%M:%S')}] Node {nid} back online")
#
# def update_training_progress(current: int, total: int):
#     with _FL_LOCK:
#         FL_STATE["training_progress"]["current"] = current
#         FL_STATE["training_progress"]["total"] = total
#
#
# def _update_node_from_ping(node_id, ip=None, status="online", rounds=None, meta=None):
#     now = time.time()
#     with _FL_LOCK:
#         node = FL_STATE["nodes"].get(node_id, {})
#         node["id"] = node_id
#         if ip:
#             node["ip"] = ip
#         node["status"] = status if status != "online" else node.get("status", "idle")
#         node["last_seen"] = now
#         node["rounds_completed"] = (
#             rounds if isinstance(rounds, int) else node.get("rounds_completed", 0)
#         )
#         if meta:
#             node["meta"] = meta
#         FL_STATE["nodes"][node_id] = node
#
#
# # ============================================================
# # 1) FL STATUS — GET /api/fl/status
# # ============================================================
# @fl_bp.route("/status", methods=["GET"])
# def fl_status_dashboard():
#     _mark_offline_nodes()
#
#     with _FL_LOCK:
#         response = {
#             "global_round": FL_STATE.get("global_round", 0),  # aggregation count
#             "current_round": FL_STATE.get("current_round", 0),  # active round
#             "round_running": FL_STATE.get("round_running", False),
#             "last_aggregation": FL_STATE.get("last_aggregation"),
#             "nodes": list(FL_STATE["nodes"].values()),
#             "metrics": FL_STATE.get("metrics", {}),
#             "training_progress": FL_STATE.get("training_progress"),
#             "metrics_history": FL_STATE.get("metrics_history", []),
#         }
#
#     return jsonify(response), 200
#
#
# # ============================================================
# # 1b) Node heartbeat — POST /api/fl/node_heartbeat
# # ============================================================
# @fl_bp.route("/node_heartbeat", methods=["POST"])
# def node_heartbeat():
#     data = request.get_json(silent=True) or {}
#     node_id = data.get("node_id") or data.get("id")
#     if not node_id:
#         return jsonify({"error": "node_id missing"}), 400
#
#     _update_node_from_ping(
#         node_id=node_id,
#         ip=data.get("ip"),
#         status=data.get("status", "online"),
#         rounds=data.get("rounds_completed"),
#         meta=data.get("meta"),
#     )
#
#     emit_log(f"[HB] Heartbeat from {node_id}")
#     save_state()
#     return jsonify({"ok": True}), 200
#
#
# # ============================================================
# # 2) START TRAINING — POST /api/fl/start_training
# # ============================================================
# @fl_bp.route("/start_training", methods=["POST"])
# def start_training_round():
#     """
#     Start the Flower federated server.
#     Flower itself controls training rounds.
#     """
#     from backend.services.server import launch_fl_server
#     emit_log("[DASHBOARD] Start Training clicked")
#
#     result = launch_fl_server()
#
#     return jsonify({
#         "status": "ok",
#         "message": "Flower server started (or already running)",
#         "result": result
#     }), 200
#
#
#
# # ============================================================
# # 3) START SERVER — POST /api/fl/start-server
# # ============================================================
# @fl_bp.route("/start-server", methods=["POST"])
# def start_server():
#     config = request.get_json(silent=True) or {}
#     result = launch_fl_server(config=config)
#     emit_log("[SERVER] FL Server started")
#     return jsonify(result), 200
#
#
# # ============================================================
# # 4) START CLIENT — POST /api/fl/start-client
# # ============================================================
# @fl_bp.route("/start-client", methods=["POST"])
# def start_client():
#     data = request.get_json(silent=True) or {}
#     result = launch_fl_client(server_address=data.get("server_address"))
#     emit_log("[CLIENT] FL Client started")
#     return jsonify(result), 200
#
# # ============================================================
# # CALLED BY FEDERATED SERVER BEFORE EACH ROUND STARTS
# # ============================================================
# def notify_round_start(round_number: int):
#     try:
#         emit_log(f"[ROUND {round_number}] Starting new training round")
#
#         # Store round start in shared state
#         with _FL_LOCK:
#             FL_STATE["current_round"] = round_number
#             FL_STATE["round_running"] = True
#             FL_STATE["last_aggregation"] = None
#             FL_STATE["training_progress"] = {
#                 "current": 0,
#                 "total": 1
#             }
#     except Exception as e:
#         emit_log(f"[ERROR] notify_round_start failed: {e}")
#
#
# # ============================================================
# # 4b) CALLED BY FEDERATED SERVER AFTER EACH ROUND
# # ============================================================
# def notify_round_complete(round_number: int, metrics: dict, clients_finished: list):
#     """Called from Flower strategy after each aggregation round."""
#     now = time.time()
#
#     with _FL_LOCK:
#         FL_STATE["global_round"] = round_number
#         FL_STATE["current_round"] = None
#         FL_STATE["round_running"] = False
#         FL_STATE["last_aggregation"] = now
#         FL_STATE["metrics"] = metrics
#
#         # -------------------------------------------------------
#         # Append to metrics history (used for graphs)
#         # -------------------------------------------------------
#         FL_STATE["metrics_history"].append({
#             "round": round_number,
#             # "epsilon_full": metrics.get("epsilon_full"),
#             # "epsilon_sampled": metrics.get("epsilon_sampled"),
#             # "sigma": metrics.get("sigma"),
#             # "q": metrics.get("q"),
#             # "round_time": metrics.get("round_time"),
#             **metrics,
#              "timestamp": now,
#
#         })
#
#         # -------------------------------------------------------
#         # Update each finished client's info
#         # -------------------------------------------------------
#         for cid in clients_finished or []:
#             node = FL_STATE["nodes"].get(cid, {})
#             node["rounds_completed"] = node.get("rounds_completed", 0) + 1
#             node["status"] = "idle"
#             node["last_seen"] = now
#
#             if metrics.get("round_time"):
#                 node["last_training_time"] = metrics["round_time"]
#
#             FL_STATE["nodes"][cid] = node
#
#         # -------------------------------------------------------
#         # Emit metrics to dashboard (safe)
#         # -------------------------------------------------------
#         if socketio is not None:
#             socketio.emit(
#                 "metric",
#                 {
#                     "round": round_number,
#                     "accuracy": metrics.get("accuracy"),
#                     "loss": metrics.get("loss"),
#                     "confusion_matrix": metrics.get("confusion_matrix"),
#                 },
#                 namespace="/metrics",
#             )
#     emit_log(f"[ROUND {round_number}] Aggregation complete")
#
# @fl_bp.route("/round_update", methods=["POST"])
# def round_update():
#     data = request.get_json() or {}
#
#     with _FL_LOCK:
#         FL_STATE["global_round"] = data.get("round", FL_STATE["global_round"])
#         FL_STATE["round_running"] = data.get("round_running", False)
#         FL_STATE["metrics"] = data.get("metrics", {})
#         FL_STATE["training_progress"] = data.get(
#             "training_progress",
#             FL_STATE["training_progress"]
#         )
#
#         if "metrics" in data:
#             FL_STATE["metrics_history"].append({
#                 **data["metrics"],
#                 "round": data.get("round"),
#                 "timestamp": time.time()
#             })
#     save_state()
#     return jsonify({"ok": True})
#
# # ============================================================
# # 5) SUPERNODE SYNC
# # ============================================================
# @fl_bp.route("/supernode/sync", methods=["POST"])
# def supernode_sync():
#     version = random.randint(1, 20)
#     emit_log(f"[SYNC] Supernode synced → version {version}")
#     return jsonify({"model_version": version, "timestamp": time.time()}), 200

# backend/routes/fl_routes.py

import os
import sys
import time
import random
import threading
import json
from flask import Blueprint, request, jsonify

from backend.services.logs_service import emit_log
from backend.extensions import socketio
from backend.services.server import launch_fl_server
from backend.services.supernode_client import launch_fl_client

# -----------------------------
# PATH FIX
# -----------------------------
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
sys.path.insert(0, PROJECT_ROOT)

# -----------------------------
# BLUEPRINT
# -----------------------------
fl_bp = Blueprint("fl", __name__)

# -----------------------------
# STATE FILE
# -----------------------------
STATE_FILE = "fl_state.json"

# -----------------------------
# SHARED FL STATE
# -----------------------------
FL_STATE = {
    "nodes": {},
    "global_round": 0,
    "current_round": None,
    "round_running": False,
    "last_aggregation": None,
    "metrics": {},
    "metrics_history": [],
    "training_progress": {
        "current": 0,
        "total": 0,
    },
}

# -----------------------------
# STATE PERSISTENCE
# -----------------------------
def save_state():
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(FL_STATE, f)
    except Exception as e:
        print("[STATE SAVE ERROR]", e)

def load_state():
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                FL_STATE.update(json.load(f))
            print("[STATE] FL_STATE restored from disk")
    except Exception as e:
        print("[STATE LOAD ERROR]", e)

load_state()

# -----------------------------
# GLOBALS
# -----------------------------
_FL_LOCK = threading.Lock()
NODE_OFFLINE_THRESHOLD = 120  # seconds

# -----------------------------
# HELPERS
# -----------------------------
def _mark_offline_nodes():
    """Mark nodes offline if heartbeat is missing."""
    now = time.time()
    with _FL_LOCK:
        for node_id, node in FL_STATE["nodes"].items():
            last_seen = node.get("last_seen", 0)
            if now - last_seen > NODE_OFFLINE_THRESHOLD:
                if node.get("status") != "offline":
                    node["status"] = "offline"
                    emit_log(f"[NODE] {node_id} marked OFFLINE")
            else:
                if node.get("status") == "offline":
                    node["status"] = "idle"
                    emit_log(f"[NODE] {node_id} back ONLINE")

def _update_node_from_ping(node_id, ip=None, status=None, rounds=None, meta=None):
    now = time.time()
    with _FL_LOCK:
        node = FL_STATE["nodes"].get(node_id, {})

        node["id"] = node_id
        if ip:
            node["ip"] = ip

        if status:
            node["status"] = status
        else:
            node["status"] = node.get("status", "idle")

        node["last_seen"] = now

        if isinstance(rounds, int):
            node["rounds_completed"] = rounds
        else:
            node["rounds_completed"] = node.get("rounds_completed", 0)

        if meta:
            node["meta"] = meta

        FL_STATE["nodes"][node_id] = node

# ============================================================
# 1) FL STATUS — GET /api/fl/status
# ============================================================
@fl_bp.route("/status", methods=["GET"])
def fl_status_dashboard():
    _mark_offline_nodes()
    save_state()

    with _FL_LOCK:
        response = {
            "global_round": FL_STATE["global_round"],
            "current_round": FL_STATE["current_round"],
            "round_running": FL_STATE["round_running"],
            "last_aggregation": FL_STATE["last_aggregation"],
            "nodes": list(FL_STATE["nodes"].values()),
            "metrics": FL_STATE["metrics"],
            "metrics_history": FL_STATE["metrics_history"],
            "training_progress": FL_STATE["training_progress"],
            "connected_nodes": sum(
                1 for n in FL_STATE["nodes"].values()
                if n.get("status") != "offline"
            ),
        }

    return jsonify(response), 200

# ============================================================
# 1b) NODE HEARTBEAT — POST /api/fl/node_heartbeat
# ============================================================
@fl_bp.route("/node_heartbeat", methods=["POST"])
def node_heartbeat():
    data = request.get_json(silent=True) or {}

    node_id = data.get("node_id") or data.get("id")
    if not node_id:
        return jsonify({"error": "node_id missing"}), 400

    _update_node_from_ping(
        node_id=node_id,
        ip=data.get("ip"),
        status=data.get("status"),
        rounds=data.get("rounds_completed"),
        meta=data.get("meta"),
    )

    emit_log(f"[HB] {node_id}")
    save_state()
    return jsonify({"ok": True}), 200

# ============================================================
# 2) START TRAINING — POST /api/fl/start_training
# ============================================================
@fl_bp.route("/start_training", methods=["POST"])
def start_training_round():
    emit_log("[DASHBOARD] Start Training clicked")
    result = launch_fl_server()
    return jsonify({
        "status": "ok",
        "message": "Flower server started",
        "result": result,
    }), 200

# ============================================================
# 3) START SERVER — POST /api/fl/start-server
# ============================================================
@fl_bp.route("/start-server", methods=["POST"])
def start_server():
    config = request.get_json(silent=True) or {}
    result = launch_fl_server(config=config)
    emit_log("[SERVER] FL Server started")
    return jsonify(result), 200

# ============================================================
# 4) START CLIENT — POST /api/fl/start-client
# ============================================================
@fl_bp.route("/start-client", methods=["POST"])
def start_client():
    data = request.get_json(silent=True) or {}
    result = launch_fl_client(server_address=data.get("server_address"))
    emit_log("[CLIENT] FL Client started")
    return jsonify(result), 200

# ============================================================
# CALLED BY FL SERVER BEFORE EACH ROUND
# ============================================================
def notify_round_start(round_number: int):
    emit_log(f"[ROUND {round_number}] Training started")

    with _FL_LOCK:
        FL_STATE["current_round"] = round_number
        FL_STATE["round_running"] = True
        FL_STATE["training_progress"] = {
            "current": 0,
            "total": 1,
        }

    save_state()

# ============================================================
# CALLED BY FL SERVER AFTER EACH ROUND
# ============================================================
def notify_round_complete(round_number: int, metrics: dict, clients_finished: list):
    now = time.time()

    with _FL_LOCK:
        FL_STATE["global_round"] = round_number
        FL_STATE["current_round"] = None
        FL_STATE["round_running"] = False
        FL_STATE["last_aggregation"] = now
        FL_STATE["metrics"] = metrics

        FL_STATE["metrics_history"].append({
            "round": round_number,
            **metrics,
            "timestamp": now,
        })

        for cid in clients_finished or []:
            node = FL_STATE["nodes"].get(cid, {})
            node["rounds_completed"] = node.get("rounds_completed", 0) + 1
            node["status"] = "idle"
            node["last_seen"] = now
            FL_STATE["nodes"][cid] = node

        if socketio:
            socketio.emit(
                "metric",
                {
                    "round": round_number,
                    "accuracy": metrics.get("accuracy"),
                    "loss": metrics.get("loss"),
                },
                namespace="/metrics",
            )

    save_state()
    emit_log(f"[ROUND {round_number}] Aggregation complete")

# ============================================================
# OPTIONAL ROUND UPDATE API
# ============================================================
@fl_bp.route("/round_update", methods=["POST"])
def round_update():
    data = request.get_json() or {}

    with _FL_LOCK:
        FL_STATE["global_round"] = data.get("round", FL_STATE["global_round"])
        FL_STATE["round_running"] = data.get("round_running", False)
        FL_STATE["metrics"] = data.get("metrics", {})
        FL_STATE["training_progress"] = data.get(
            "training_progress", FL_STATE["training_progress"]
        )

        if "metrics" in data:
            FL_STATE["metrics_history"].append({
                **data["metrics"],
                "round": data.get("round"),
                "timestamp": time.time(),
            })

    save_state()
    return jsonify({"ok": True})

# ============================================================
# SUPERNODE SYNC (OPTIONAL)
# ============================================================
@fl_bp.route("/supernode/sync", methods=["POST"])
def supernode_sync():
    version = random.randint(1, 20)
    emit_log(f"[SYNC] Supernode synced → version {version}")
    return jsonify({
        "model_version": version,
        "timestamp": time.time(),
    }), 200
