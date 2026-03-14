#!/usr/bin/env python3
"""
Federated Learning Configuration Helper
Auto-detects your system and helps configure paths
"""

import sys
import os
import subprocess
from pathlib import Path

def get_system_info():
    """Get system information"""
    system_type = sys.platform
    hostname = os.environ.get('COMPUTERNAME') or os.environ.get('HOSTNAME') or 'Unknown'
    
    return {
        'system': system_type,
        'hostname': hostname,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }

def get_ip_address():
    """Get the machine's IP address"""
    import socket
    
    try:
        # Get hostname
        hostname = socket.gethostname()
        
        # Get IP address (tries to connect to external host)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Warning: Could not determine IP address: {e}")
        return "127.0.0.1"

def check_dependencies():
    """Check if required packages are installed"""
    required = ['torch', 'flwr', 'numpy', 'pandas', 'sklearn']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    return missing

def check_cuda():
    """Check if CUDA is available"""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

def main():
    print("\n" + "="*60)
    print("🔧 Federated Learning Configuration Helper")
    print("="*60 + "\n")
    
    # System Info
    info = get_system_info()
    print(f"📱 System Information:")
    print(f"   Platform: {info['system']}")
    print(f"   Hostname: {info['hostname']}")
    print(f"   Python: {info['python_version']}")
    
    # IP Address
    ip = get_ip_address()
    print(f"\n🌐 Network Information:")
    print(f"   IP Address: {ip}")
    print(f"   Server Address: {ip}:8082")
    
    # Dependencies
    print(f"\n📦 Checking Dependencies...")
    missing = check_dependencies()
    if missing:
        print(f"   ⚠️  Missing packages: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
    else:
        print(f"   ✅ All dependencies installed")
    
    # CUDA
    print(f"\n💻 Compute:")
    if check_cuda():
        import torch
        print(f"   ✅ CUDA Available")
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
    else:
        print(f"   ℹ️  CUDA not available (will use CPU)")
    
    # Project Structure
    print(f"\n📁 Project Structure:")
    project_root = Path(__file__).parent.parent
    required_dirs = ['src', 'federated', 'Dataset', 'backend']
    for d in required_dirs:
        path = project_root / d
        status = "✅" if path.exists() else "❌"
        print(f"   {status} {d}/")
    
    # Configuration Template
    print(f"\n📋 Configuration Template:")
    print(f"""
For WINDOWS Server:
  python federated/start_server.py --server-address {ip}:8082 --num-rounds 3

For LINUX Client (connect to Windows):
  python federated/start_client.py --server-address {ip}:8082 --client-id 2

For Windows Client (same machine):
  python federated/start_client.py --server-address {ip}:8082 --client-id 1
""")
    
    print("="*60 + "\n")
    print("✨ Configuration check complete!")
    print("Next: Run the server and connect clients!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
