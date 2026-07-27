from __future__ import annotations
import os
from pathlib import Path

CONFIG_FILE = Path.home() / ".conrrad" / "config.yaml"

def main() -> int:
    print("\n☁️ Connecting to Conrrad Cloud...\n")

    api_key = input("Enter API key: ").strip()

    if not api_key:
        print("❌ API key required")
        return 1

    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    CONFIG_FILE.write_text(
        f"api_key: {api_key}\n"
        "classifier_endpoint: https://api.conrrados.com\n"
    )

    print("✅ Connected to cloud\n")
    return 0
