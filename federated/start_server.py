#!/usr/bin/env python3
"""
Multi-Client Federated Server
Run this on one machine (e.g., your Windows laptop) to serve all clients
"""

import sys
import os

# Fix Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import argparse
from federated.server import start_fl_server
from federated.config import FLOWER_SERVER_ADDRESS, NUM_ROUNDS

def main():
    parser = argparse.ArgumentParser(description="Start Federated Learning Server")
    parser.add_argument("--server-address", type=str, default=FLOWER_SERVER_ADDRESS,
                        help="Server address (default: 127.0.0.1:8082)")
    parser.add_argument("--num-rounds", type=int, default=NUM_ROUNDS,
                        help="Number of rounds (default: 3)")
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"🚀 Starting Federated Learning Server")
    print(f"{'='*60}")
    print(f"Server Address: {args.server_address}")
    print(f"Number of Rounds: {args.num_rounds}")
    print(f"\n⏳ Waiting for clients to connect...")
    print(f"{'='*60}\n")
    
    start_fl_server(num_rounds=args.num_rounds, server_address=args.server_address)

if __name__ == "__main__":
    main()
