#!/bin/bash
# Federated Learning Client Launcher for Linux

echo ""
echo "============================================================"
echo "Starting Federated Learning Client"
echo "============================================================"
echo ""

# Get project root
cd "$(dirname "$0")"

# Parse arguments
SERVER_ADDRESS="${1:-127.0.0.1:8082}"
CLIENT_ID="${2:-1}"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

echo "Server Address: $SERVER_ADDRESS"
echo "Client ID: $CLIENT_ID"
echo ""

# Start client
python3 federated/start_client.py --server-address "$SERVER_ADDRESS" --client-id "$CLIENT_ID"
