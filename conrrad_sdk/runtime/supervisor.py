"""VS-06 Runtime supervisor — restart on crash without mutating FM/identity."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def supervise(
    repo_root: Path,
    citizen_id: str,
    citizen_dir: Path | None,
    runtime_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8530,
    max_restarts: int = 3,
    backoff_s: float = 0.5,
) -> int:
    runtime_dir.mkdir(parents=True, exist_ok=True)
    state_path = runtime_dir / "state.json"
    restart_count = 0
    if state_path.is_file():
        import json

        try:
            restart_count = int(json.loads(state_path.read_text()).get("restart_count", 0))
        except (json.JSONDecodeError, ValueError):
            restart_count = 0

    child: subprocess.Popen | None = None

    def _terminate(signum: int, _frame) -> None:
        if child and child.poll() is None:
            child.terminate()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _terminate)
    signal.signal(signal.SIGINT, _terminate)

    sdk_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-m",
        "conrrad_sdk.runtime.server_main",
        "--repo-root",
        str(repo_root),
        "--citizen",
        citizen_id,
        "--runtime-dir",
        str(runtime_dir),
        "--host",
        host,
        "--port",
        str(port),
    ]
    if citizen_dir:
        cmd.extend(["--citizen-dir", str(citizen_dir)])

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{sdk_root.parent}:{repo_root / 'services'}:{env.get('PYTHONPATH', '')}"

    while restart_count <= max_restarts:
        child = subprocess.Popen(cmd, env=env)
        code = child.wait()
        restart_count += 1
        if state_path.is_file():
            import json

            data = json.loads(state_path.read_text())
            data["restart_count"] = restart_count
            state_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        if restart_count > max_restarts:
            return code
        time.sleep(backoff_s)

    return 1
