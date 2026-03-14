# Federated Learning Setup: Windows + Linux

This guide helps you set up federated learning training across **two systems**: a Windows laptop and a Linux machine.

## Architecture Overview

```
┌─────────────────────┐
│ Server (Windows)    │
│ Port: 8082          │─────────┬──────────────┐
│ Coordinates Training│         │              │
└─────────────────────┘         │              │
                                │              │
                        ┌───────▼──────┐ ┌────▼──────────┐
                        │ Windows Client│ │ Linux Client  │
                        │ (Local/Remote)│ │ (Separate PC) │
                        └───────────────┘ └───────────────┘
```

## Prerequisites

### Both Windows and Linux Systems
- Python 3.8+
- PyTorch (CPU or GPU)
- Flower (Federated Learning framework)
- Project dependencies

```bash
# Install dependencies
pip install -r backend/requirements.txt
pip install flwr
pip install torch torchvision torchaudio
```

## Step 1: Clone/Sync Project to Both Systems

### Windows (Server Machine)
```bash
cd c:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project
```

### Linux (Client Machine)
```bash
# Clone from GitHub
git clone https://github.com/Varshapandu/NeuroFusion-.git
cd NeuroFusion-
```

## Step 2: Set Up Python Environments

### Windows
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
pip install flwr
```

### Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install flwr
```

## Step 3: Configure Federated Learning Settings

Edit `federated/config.py` on **both systems** to match:

```python
# ✅ Same on both machines
NUM_ROUNDS = 3              # Number of communication rounds
TOTAL_CLIENTS = 2           # Total number of clients
CLIENTS_PER_ROUND = 2       # Clients per round
LOCAL_EPOCHS = 1            # Local training epochs per client
BATCH_SIZE = 32             # Batch size for training
```

## Step 4: Get Your Windows Machine's IP Address

### On Windows (Server)
```powershell
ipconfig
# Look for "IPv4 Address" under your network adapter
# Example: 192.168.1.10 or 10.0.0.5
```

**Note:** Use the IP address on the same network as your Linux machine!

## Step 5: Start the Server (Windows)

### Option A: Local Testing (Both on Same Windows Machine)
```powershell
cd C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project
.\.venv\Scripts\Activate.ps1

# Start server
python federated/start_server.py --server-address 0.0.0.0:8082 --num-rounds 3
```

### Option B: Multi-System (Windows Server + Linux Client)
```powershell
cd C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project
.\.venv\Scripts\Activate.ps1

# Get your Windows IP (from ipconfig above)
# Replace 192.168.1.10 with your actual IP
python federated/start_server.py --server-address 192.168.1.10:8082 --num-rounds 3
```

**Expected Output:**
```
============================================================
🚀 Starting Federated Learning Server
============================================================
Server Address: 192.168.1.10:8082
Number of Rounds: 3
⏳ Waiting for clients to connect...
============================================================
```

## Step 6: Start the Clients

### Client 1: Windows (Local)
Open a **new PowerShell window**:
```powershell
cd C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project
.\.venv\Scripts\Activate.ps1

# Connect to the server
python federated/start_client.py --server-address 192.168.1.10:8082 --client-id 1
```

### Client 2: Linux (Separate Machine)
On your Linux machine:
```bash
cd ~/path/to/NeuroFusion-
source venv/bin/activate

# Replace 192.168.1.10 with Windows server IP
python federated/start_client.py --server-address 192.168.1.10:8082 --client-id 2
```

## Step 7: Monitor the Training

The server terminal will show:
```
Round 1/3
- Waiting for 2 clients to submit updates...
- Client 1 (Windows) connected ✓
- Client 2 (Linux) connected ✓
- Aggregating model updates...
- Round 1 complete

Round 2/3
...
```

## Troubleshooting

### ❌ Connection Refused
```
ConnectionRefusedError: Failed to connect to 192.168.1.10:8082
```
**Solution:**
- Verify server is running: Check Windows firewall
- Check IP address: Make sure you're using the correct Windows IP
- Enable Windows Firewall rules:
  ```powershell
  New-NetFirewallRule -DisplayName "Flower FL" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8082
  ```

### ❌ Module Not Found
```
ModuleNotFoundError: No module named 'src'
```
**Solution:**
- Check that you're in the project root directory
- Verify Python path is set: `sys.path.insert(0, PROJECT_ROOT)`

### ❌ Dataset Not Found
```
FileNotFoundError: Dataset/train_split.csv
```
**Solution:**
- Ensure dataset is prepared: `python prepare_split_csvs.py`
- Check Dataset/ folder exists with split CSV files

### ❌ CUDA/GPU Issues
```
torch.cuda.OutOfMemoryError
```
**Solution:**
- Reduce `BATCH_SIZE` in `federated/config.py`
- Use CPU: Models will use CPU automatically if CUDA unavailable

## Testing Locally First (Optional)

To test on **one Windows machine** with 2 clients:

```powershell
# Terminal 1: Start server
python federated/start_server.py

# Terminal 2: Client 1
python federated/start_client.py --client-id 1

# Terminal 3: Client 2
python federated/start_client.py --client-id 2
```

## Advanced: Network Configuration

### If on Same LAN but Different Subnets
- Use a VPN or SSH tunnel
- For SSH tunnel on Linux:
  ```bash
  ssh -L 8082:192.168.1.10:8082 user@windows_machine
  ```

### If Over the Internet (Not Recommended for Demo)
- Set up a reverse proxy with ngrok:
  ```bash
  # On Windows server
  ngrok tcp 8082
  # Use the provided URL for clients
  ```

## Expected Results

After 3 rounds:
- **Server**: Aggregates model updates from both Windows and Linux clients
- **Clients**: Train locally and communicate updates via Flower
- **Model**: Improves (though slightly) with each round
- **Privacy**: Updates are differentially private (noise added)

## Next Steps

1. ✅ Verify training works locally (Windows only)
2. ✅ Add Linux machine to same network
3. ✅ Modify server address to Windows machine IP
4. ✅ Run synchronized federated training
5. ✅ Monitor metrics: loss, accuracy, epsilon (privacy budget)

---

For questions or issues, check server terminal output and client logs!
