import os
import sys

CURRENT_DIR = os.path.dirname(__file__)           # backend/routes
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
sys.path.insert(0, PROJECT_ROOT)

from flask import Blueprint, request, jsonify
from services.agent_service import run_agent_query
import time

agent_bp = Blueprint("agent_bp", __name__)


# ============================================================
# ORIGINAL AGENT ROUTE (UNMODIFIED)
# ============================================================
@agent_bp.route("/agent", methods=["POST"])
def agent_chat():
    data = request.get_json(silent=True) or {}
    query = data.get("query")

    if not query:
        return jsonify({"error": "No query provided"}), 400

    response = run_agent_query(query)

    # A clean enriched response object
    return jsonify({
        "response": response,
        "timestamp": time.time()
    })


# ============================================================
# OPTIONAL: HEALTH CHECK ROUTE FOR DEBUGGING
# ============================================================
@agent_bp.route("/agent/health", methods=["GET"])
def agent_health():
    """
    Simple route for checking whether agent service is available.
    (Does NOT call the agent model, so it's fast.)
    """
    return jsonify({
        "module": "agent_service",
        "status": "active",
        "time": time.time()
    })
