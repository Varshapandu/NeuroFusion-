#!/usr/bin/env python3
"""
Standalone Federated Learning Client
Run this on each machine (Windows or Linux) to train locally and communicate with the server
"""

import sys
import os

# Fix Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import argparse
import logging
import flwr as fl
from federated.supernode_client import FlowerClient
from federated.config import FLOWER_SERVER_ADDRESS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Start Federated Learning Client")
    parser.add_argument("--server-address", type=str, default=FLOWER_SERVER_ADDRESS,
                        help="Server address (e.g., 192.168.1.10:8082 or localhost:8082)")
    parser.add_argument("--client-id", type=int, default=1,
                        help="Client ID (for tracking purposes)")
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"🤖 Starting Federated Learning Client")
    print(f"{'='*60}")
    print(f"Server Address: {args.server_address}")
    print(f"Client ID: {args.client_id}")
    print(f"Platform: {sys.platform}")
    print(f"\n📡 Attempting to connect to server...")
    print(f"{'='*60}\n")
    
    try:
        client = FlowerClient()
        fl.client.start_numpy_client(
            server_address=args.server_address,
            client=client
        )
    except ConnectionRefusedError:
        logger.error(f"❌ Failed to connect to server at {args.server_address}")
        logger.error("Make sure the server is running and the address is correct.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Client error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
