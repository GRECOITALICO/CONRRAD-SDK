from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

def _find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for _ in range(8):
        if (current / ".conrrad-evidence" / "founder_model_v1.json").is_file():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def _fetch_json(url: str, timeout: float = 3.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _print_help() -> None:
    print("Usage: conrrad runtime <start|stop|status|health> [citizen]")
    print("  start   — supervised platform runtime (VS-06)")
    print("  health  — GET /health against running runtime")


def cmd_start(args: argparse.Namespace) -> int:
    repo_root = args.repo_root or _find_repo_root(Path.cwd())
    if repo_root is None:
        print("❌ Cannot locate CONRRAD repo root")
        return 2

    citizen_dir = args.citizen_dir
    if citizen_dir is None and args.citizen:
        candidate = Path.cwd() / args.citizen
        if (candidate / "birth_manifest.json").is_file():
            citizen_dir = candidate

    runtime_dir = args.runtime_dir or (repo_root / ".conrrad-evidence" / "runtime" / args.citizen)
    pid_file = runtime_dir / "supervisor.pid"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    if pid_file.is_file():
        old_pid = int(pid_file.read_text().strip())
        try:
            os.kill(old_pid, 0)
            print(f"⚠ Runtime supervisor already running (pid {old_pid})")
            return 0
        except OSError:
            pid_file.unlink(missing_ok=True)

    sdk_root = Path(__file__).resolve().parents[1]
    cmd = [
        sys.executable,
        "-m",
        "conrrad_sdk.runtime.supervisor_main",
        "--repo-root",
        str(repo_root),
        "--citizen",
        args.citizen,
        "--runtime-dir",
        str(runtime_dir),
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    if citizen_dir:
        cmd.extend(["--citizen-dir", str(citizen_dir)])

    env = {**os.environ, "PYTHONPATH": f"{sdk_root.parent}:{repo_root / 'services'}"}
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pid_file.write_text(str(proc.pid) + "\n", encoding="utf-8")

    deadline = time.time() + 10
    base = f"http://{args.host}:{args.port}"
    while time.time() < deadline:
        try:
            health = _fetch_json(f"{base}/health")
            if health.get("status") == "ok":
                print(f"✅ Runtime started: {base}/health (supervisor pid {proc.pid})")
                print(f"   citizen: {args.citizen}")
                print(f"   runtime_dir: {runtime_dir}")
                return 0
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            time.sleep(0.3)

    print("❌ Runtime failed to become healthy within 10s")
    return 1


def cmd_stop(args: argparse.Namespace) -> int:
    runtime_dir = args.runtime_dir
    if runtime_dir is None:
        repo = args.repo_root or _find_repo_root(Path.cwd())
        if repo is None:
            return 2
        runtime_dir = repo / ".conrrad-evidence" / "runtime" / args.citizen
    pid_file = runtime_dir / "supervisor.pid"
    if not pid_file.is_file():
        print("No supervisor pid file")
        return 0
    import os
    import signal

    pid = int(pid_file.read_text().strip())
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    pid_file.unlink(missing_ok=True)
    print(f"Stopped supervisor pid {pid}")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    base = f"http://{args.host}:{args.port}"
    try:
        data = _fetch_json(f"{base}/health")
    except Exception as exc:
        print(f"❌ Health check failed: {exc}")
        return 1
    print(json.dumps(data, indent=2))
    return 0 if data.get("status") == "ok" else 1


def cmd_status(args: argparse.Namespace) -> int:
    repo = args.repo_root or _find_repo_root(Path.cwd())
    if repo is None:
        return 2
    runtime_dir = args.runtime_dir or (repo / ".conrrad-evidence" / "runtime" / args.citizen)
    state_path = runtime_dir / "state.json"
    if not state_path.is_file():
        print("No runtime state")
        return 1
    print(state_path.read_text(encoding="utf-8"))
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "runtime":
        argv = argv[1:]

    parser = argparse.ArgumentParser(prog="conrrad runtime", add_help=False)
    parser.add_argument("action", nargs="?", choices=["start", "stop", "status", "health"])
    parser.add_argument("citizen", nargs="?", default="scout")
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--citizen-dir", type=Path)
    parser.add_argument("--runtime-dir", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8530)
    parser.add_argument("-h", "--help", action="store_true")
    args, _ = parser.parse_known_args(argv)

    if args.help or not args.action:
        _print_help()
        return 0

    if args.action == "start":
        return cmd_start(args)
    if args.action == "stop":
        return cmd_stop(args)
    if args.action == "health":
        return cmd_health(args)
    if args.action == "status":
        return cmd_status(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
