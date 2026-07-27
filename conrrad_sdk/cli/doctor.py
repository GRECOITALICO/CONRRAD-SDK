from __future__ import annotations
import subprocess
import urllib.request
import sys
import shutil

def check_http(url: str) -> bool:
    try:
        urllib.request.urlopen(url, timeout=2)
        return True
    except Exception:
        return False

def check_router():
    try:
        from conrrad_sdk.router import IntelligentRouter
        return True
    except Exception:
        return False

def main() -> int:
    deep = "--deep" in sys.argv

    print("\n🩺 Conrrad Doctor\n")

    conrrad_bin = shutil.which("conrrad")
    if conrrad_bin:
        cli_ok = subprocess.run(["conrrad", "--help"], capture_output=True).returncode == 0
    else:
        cli_ok = subprocess.run([sys.executable, "-m", "conrrad_sdk.cli", "--help"], capture_output=True).returncode == 0

    checks = {
        "CLI": cli_ok,
    }

    if deep:
        checks.update({
            "Router import": check_router(),
            "Qdrant": check_http("http://localhost:6333/healthz"),
        })

    all_ok = True

    for name, status in checks.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
        if not status:
            all_ok = False

    print()
    return 0 if all_ok else 1
