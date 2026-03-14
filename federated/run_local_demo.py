# federated/run_local_demo.py
import threading
import time
from federated.server import start_fl_server
from federated.supernode_client import FlowerClient
import flwr as fl
from federated.config import FLOWER_SERVER_ADDRESS, NUM_ROUNDS

def run_server():
    start_fl_server(num_rounds=NUM_ROUNDS, server_address=FLOWER_SERVER_ADDRESS)

if __name__ == "__main__":
    # Start server thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(2.0)

    # Start a client that connects to the server (in-process)
    print("Starting local Flower client (demo).")
    fl.client.start_numpy_client(server_address=FLOWER_SERVER_ADDRESS, client=FlowerClient())
