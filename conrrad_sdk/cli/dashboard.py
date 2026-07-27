from __future__ import annotations
import subprocess
import sys

def main() -> int:
    print("\n📊 Starting Conrrad Dashboard on http://0.0.0.0:8503 ...\n")
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "conrrad_sdk.web_dashboard.server:app",
        "--host", "0.0.0.0",
        "--port", "8503"
    ])
    return 0
