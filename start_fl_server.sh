#!/bin/bash
# Federated Learning Server Launcher for Linux

echo ""
echo "============================================================"
echo "Starting Federated Learning Server"
echo "============================================================"
echo ""

# Get project root
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

# Get IP address
IP=$(hostname -I | awk '{print $1}')
if [ -z "$IP" ]; then
    IP="127.0.0.1"
fi

echo "Server IP Address: $IP"
echo "Server Port: 8082"
echo ""

# Start server
python3 federated/start_server.py --server-address $IP:8082 --num-rounds 3
