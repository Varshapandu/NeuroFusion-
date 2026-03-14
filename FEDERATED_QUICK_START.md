# Quick Start: Federated Learning on Windows + Linux

## TL;DR - Get Started in 5 Minutes

### Step 1: Prepare Both Systems
```bash
# On both Windows and Linux:
pip install -r backend/requirements.txt
pip install flwr

# Prepare dataset (if not done already)
python prepare_split_csvs.py
```

### Step 2: Check Your Configuration
```bash
# On Windows (Server)
python federated/check_config.py
# Note: Your IP address (e.g., 192.168.1.10)

# On Linux (Client)
python3 federated/check_config.py
```

### Step 3: Start Server (Windows)

**Option A - Manual:**
```powershell
cd C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project
.\.venv\Scripts\Activate.ps1
python federated/start_server.py --server-address 192.168.1.10:8082 --num-rounds 3
```

**Option B - Batch Script (Easiest):**
```powershell
start_fl_server.bat
# This automatically detects your IP and starts the server
```

### Step 4: Start Clients

#### Windows Client (2nd Terminal on Windows)
**Option A - Manual:**
```powershell
cd C:\Users\varsh\OneDrive\Desktop\Harmful_Brain_activity_project
.\.venv\Scripts\Activate.ps1
python federated/start_client.py --server-address 192.168.1.10:8082 --client-id 1
```

**Option B - Batch Script (Easiest):**
```powershell
start_fl_client.bat 192.168.1.10:8082 1
```

#### Linux Client (On Your Linux Machine)
```bash
cd ~/NeuroFusion-
source venv/bin/activate
./start_fl_client.sh 192.168.1.10:8082 2
```

Or manually:
```bash
python3 federated/start_client.py --server-address 192.168.1.10:8082 --client-id 2
```

---

## Windows Terminal Layout (Recommended)

| Terminal 1 | Terminal 2 | Terminal 3 |
|-----------|-----------|-----------|
| **Server** | **Client 1** | **Client 2** |
| `start_fl_server.bat` | `start_fl_client.bat 192.168.1.10:8082 1` | Client on Linux machine |

---

## Expected Output

### Server (Windows)
```
============================================================
🚀 Starting Federated Learning Server
============================================================
Server Address: 192.168.1.10:8082
Number of Rounds: 3
⏳ Waiting for clients to connect...
============================================================

[INFO] Server started at 192.168.1.10:8082
[INFO] Round 1/3: Waiting for 2 clients...
[INFO] Client 1 (Windows) connected ✓
[INFO] Client 2 (Linux) connected ✓
[INFO] Aggregating updates...
[INFO] Round 1 complete - Loss: 1.234
...
```

### Client (Windows & Linux)
```
============================================================
🤖 Starting Federated Learning Client
============================================================
Server Address: 192.168.1.10:8082
Client ID: 1
Platform: win32
📡 Attempting to connect to server...
============================================================
[INFO] Connected to server
[INFO] Round 1: Training locally...
[INFO] Local epochs: 1
[INFO] Training complete - Sending update
[INFO] Waiting for next round...
```

---

## Common Issues & Fixes

### ❌ "Connection refused" on Client

**Problem:**
```
ConnectionRefusedError: [Errno 111] Connect call failed
```

**Fixes:**
1. **Check server is running** → Terminal 1 should show "Waiting for clients..."
2. **Check IP address** → Use your actual Windows IP (e.g., `ipconfig`)
3. **Check firewall** → Windows might be blocking port 8082
   ```powershell
   # Allow port 8082 in Windows Firewall
   New-NetFirewallRule -DisplayName "Flower" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8082
   ```

### ❌ "Cannot find module src"

**Problem:**
```
ModuleNotFoundError: No module named 'src'
```

**Fix:**
- Make sure you're in the **project root directory**
- NOT in the `federated/` subdirectory
- Check: `ls src/` or `dir src` should show model files

### ❌ "Dataset not found"

**Problem:**
```
FileNotFoundError: Dataset/train_split.csv
```

**Fix:**
```bash
python prepare_split_csvs.py
# This creates the required CSV files
```

### ❌ "Out of memory" error

**Fix:** Reduce batch size in terminal before starting:
```bash
# Windows
set BATCH_SIZE=16

# Linux
export BATCH_SIZE=16
```

---

## Performance Tips

- **Slow Training?** → Reduce `BATCH_SIZE` or `LOCAL_EPOCHS`
- **Network Latency?** → Reduce `NUM_ROUNDS` (set to 2 or 3)
- **Memory Issues?** → on Linux, set `BATCH_SIZE=8`

---

## What's Happening with Federated Learning?

```
Round 1:
  [Server] "Hey clients, use this model"
  [Windows] "Training locally... 📊"
  [Linux] "Training locally... 📊"
  [Server] "Thanks! Averaging your models..."
  → New model = Average(Windows_model, Linux_model)

Round 2:
  [Server] "Using the averaged model, train again"
  [Windows] "Training locally... 📊"
  [Linux] "Training locally... 📊"
  [Server] "Averaging again..."
  → Model improves 📈

Round 3:
  (Repeat)
  ...Training complete! ✅
```

---

## Next Steps

1. ✅ Run locally on Windows only (test first!)
2. ✅ Add Linux machine to same network
3. ✅ Update server address to Windows IP
4. ✅ Run synchronized federated training
5. ✅ Monitor convergence & privacy metrics

---

## Troubleshooting Commands

```powershell
# Windows - Check IP
ipconfig | findstr "IPv4"

# Windows - Check if port is open
netstat -ano | findstr 8082

# Linux - Check IP
hostname -I

# Linux - Check if port is accessible
telnet 192.168.1.10 8082
```

Happy federated learning! 🚀
