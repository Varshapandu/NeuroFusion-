import os
import sys

# -----------------------------
# PATH FIXES
# -----------------------------
# backend/app.py → go one level up to project root
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
sys.path.insert(0, PROJECT_ROOT)

# -----------------------------
# FLASK + SOCKETIO IMPORTS
# -----------------------------
from flask import Flask
from flask_cors import CORS
from backend.extensions import socketio

# -----------------------------
# BLUEPRINT IMPORTS
# -----------------------------
from backend.routes.analysis_routes import analysis_bp
from backend.routes.agent_routes import agent_bp
from backend.routes.fl_routes import fl_bp

# -----------------------------
# LOG SERVICE IMPORTS
# -----------------------------
from backend.services.logs_service import set_socketio, start_background_log_stream


# ============================================================
# CREATE FLASK APP (must be before SocketIO)
# ============================================================
app = Flask(__name__)
CORS(app,
     resources={r"/api/*": {
         "origins": "*",
         "allow_headers": "*",
         "methods": ["GET", "POST", "OPTIONS"],
     }},
     supports_credentials=True)

# ============================================================
# INITIALIZE SOCKET.IO (single shared instance)
# ============================================================
socketio.init_app(app)


# Give the logs system access to socketio
set_socketio(socketio)

# Start background heartbeat logs (safe)
try:
    start_background_log_stream()
except RuntimeError:
    # When Flask debug reloader triggers twice
    pass


# ============================================================
# REGISTER BLUEPRINTS
# ============================================================
app.register_blueprint(analysis_bp, url_prefix="/api")
app.register_blueprint(agent_bp, url_prefix="/api")
app.register_blueprint(fl_bp, url_prefix="/api/fl")


# ============================================================
# BASIC ROUTE
# ============================================================
@app.route("/")
def home():
    return {"message": "NeuroFusion Flask Backend Running!"}


# ============================================================
# SOCKETIO LOG EVENTS
# ============================================================
@socketio.on("connect", namespace="/logs")
def logs_connect():
    print("Client connected to /logs")


@socketio.on("disconnect", namespace="/logs")
def logs_disconnect():
    print("Client disconnected from /logs")


# Metrics namespace (even if passive)
# @socketio.on("connect", namespace="/metrics")
# def metrics_connect():
#     print("Client connected to /metrics")

@app.route('/favicon.ico')
def favicon():
    return '', 204


# ============================================================
# RUN THE SERVER
# ============================================================
if __name__ == "__main__":
    print("🚀 NeuroFusion Backend Starting on http://127.0.0.1:5000")
    socketio.run(app, debug=True, host="127.0.0.1", port=5000 )
