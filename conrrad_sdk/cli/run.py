from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple


def _parse_run_args(argv: list[str]) -> Tuple[Optional[str], bool, list[str]]:
    project: Optional[str] = None
    legacy = False
    rest: list[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--legacy":
            legacy = True
            i += 1
            continue
        if token.startswith("-"):
            rest.append(token)
            if token in ("--task-type", "--input", "--api-key", "--base-url") and i + 1 < len(argv):
                rest.append(argv[i + 1])
                i += 2
                continue
            i += 1
            continue
        if project is None:
            project = token
            i += 1
            continue
        rest.append(token)
        i += 1
    return project, legacy, rest


def _resolve_project_dir(name: Optional[str], cwd: Optional[Path] = None) -> Path:
    base = cwd or Path.cwd()
    if name:
        nested = base / name
        if (nested / "conrrad.yaml").is_file():
            return nested.resolve()
        if (base / "conrrad.yaml").is_file() and base.name == name:
            return base.resolve()
        manifest_path = base / "manifest.json"
        if (base / "conrrad.yaml").is_file() and manifest_path.is_file():
            try:
                manifest_id = json.loads(manifest_path.read_text(encoding="utf-8")).get("id")
                if manifest_id == name:
                    return base.resolve()
            except (json.JSONDecodeError, OSError):
                pass
        raise FileNotFoundError(f"Project not found: {nested} (missing conrrad.yaml)")
    if (base / "conrrad.yaml").is_file():
        return base.resolve()
    raise FileNotFoundError(
        "No project in current directory. Usage: conrrad run <project>  or  cd <project> && conrrad run"
    )


def _wait_for_health(url: str, timeout: float = 30.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.5)
    return False


def _stop_stale_runtime(pid_file: Path) -> None:
    if not pid_file.is_file():
        return
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
    except ValueError:
        pid_file.unlink(missing_ok=True)
        return
    try:
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.3)
    except ProcessLookupError:
        pass
    pid_file.unlink(missing_ok=True)


def _is_local_quickstart(project_dir: Path) -> bool:
    manifest_path = project_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if data.get("template") == "hello" or data.get("mode") == "local-quickstart":
                return True
        except (json.JSONDecodeError, OSError):
            pass
    yaml_path = project_dir / "conrrad.yaml"
    if yaml_path.is_file():
        try:
            text = yaml_path.read_text(encoding="utf-8")
            if "local-quickstart" in text or "template: hello" in text:
                return True
        except OSError:
            pass
    return False


def run_local_quickstart(project_dir: Path) -> int:
    main_py = project_dir / "main.py"
    if not main_py.is_file():
        print(f"❌ Missing main.py in {project_dir}")
        return 2

    print("✔ Agent started")
    proc = subprocess.run(
        [sys.executable, str(main_py)],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
    )
    if proc.stdout.strip():
        print(proc.stdout.rstrip())
    if proc.returncode != 0:
        if proc.stderr.strip():
            print(proc.stderr.rstrip(), file=sys.stderr)
        print("❌ Task failed")
        return proc.returncode or 1

    print("✔ Task completed")
    print("✔ Audit trail available")
    print("✔ Cost: Local execution")
    print("✔ Done")
    return 0


def run_project(project_name: Optional[str] = None) -> int:
    try:
        project_dir = _resolve_project_dir(project_name)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 2

    if _is_local_quickstart(project_dir):
        return run_local_quickstart(project_dir)

    port = int(os.getenv("CONRRAD_DEV_PORT", "8080"))
    health_url = f"http://127.0.0.1:{port}/health"
    workspace = project_dir / "workspace"
    workspace.mkdir(exist_ok=True)
    pid_file = workspace / ".runtime.pid"
    log_file = workspace / "runtime.log"

    _stop_stale_runtime(pid_file)

    cmd = [
        sys.executable,
        "-m",
        "conrrad_sdk.cli.project_server",
        "--port",
        str(port),
        "--project-dir",
        str(project_dir),
    ]
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"\n=== run {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} ===\n")
        proc = subprocess.Popen(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    pid_file.write_text(str(proc.pid), encoding="utf-8")

    if proc.poll() is not None:
        print(f"❌ Runtime failed to start (exit {proc.returncode}). See {log_file}")
        return 1

    if not _wait_for_health(health_url):
        print(f"❌ Health check failed: {health_url}")
        return 1

    manifest_id = project_dir.name
    manifest_path = project_dir / "manifest.json"
    if manifest_path.is_file():
        manifest_id = json.loads(manifest_path.read_text(encoding="utf-8")).get("id", manifest_id)

    print("Runtime started")
    print("Health: PASS")
    print(f"Project: {manifest_id}")
    print(f"Health URL: {health_url}")
    print(f"PID: {proc.pid} · log: {log_file}")
    return 0


def _legacy_main(argv: list[str]) -> int:
    task_type = "simple"
    task_input = ""
    api_key = os.getenv("CONRRAD_API_KEY", "")
    base_url = os.getenv("CONRRAD_BASE_URL", "http://localhost:8000")
    legacy = False

    i = 0
    while i < len(argv):
        token = argv[i]
        if token == "--task-type" and i + 1 < len(argv):
            task_type = argv[i + 1]
            i += 2
            continue
        if token == "--input" and i + 1 < len(argv):
            task_input = argv[i + 1]
            i += 2
            continue
        if token == "--api-key" and i + 1 < len(argv):
            api_key = argv[i + 1]
            i += 2
            continue
        if token == "--base-url" and i + 1 < len(argv):
            base_url = argv[i + 1]
            i += 2
            continue
        if token == "--legacy":
            legacy = True
            i += 1
            continue
        if token in ("-h", "--help"):
            _print_help()
            return 0
        i += 1

    if not api_key:
        print("❌ Missing API key. Use --api-key or set CONRRAD_API_KEY.")
        return 2

    endpoint = "/api/v1/sandbox/execute" if legacy else "/api/v1/sandbox/execute-v2"
    req = urllib.request.Request(
        url=f"{base_url.rstrip('/')}{endpoint}",
        method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        data=json.dumps({"task_type": task_type, "input": task_input}).encode("utf-8"),
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read().decode("utf-8") if exc.fp else "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = {"detail": raw or str(exc)}

    if status >= 400:
        print(f"❌ Execution failed ({status}): {data.get('detail', data)}")
        return 1

    print("✅ Execution (legacy sandbox)")
    print(f"Execution ID: {data.get('execution_id')}")
    return 0


def _print_help() -> None:
    print("Usage: conrrad run [<project>]")
    print("       cd <project> && conrrad run")
    print("       conrrad run --legacy [--task-type ...]  (remote sandbox API)")
    print("")
    print("Quick Start (hello): local run — no Docker")
    print("Full projects (e.g. harvey): dev runtime with /health on :8080")
    print("Env: CONRRAD_DEV_PORT (default 8080)")


def main() -> int:
    argv = sys.argv[2:] if len(sys.argv) >= 2 and sys.argv[1] == "run" else sys.argv[1:]

    if argv and argv[0] in ("-h", "--help"):
        _print_help()
        return 0

    if not argv:
        return run_project(None)

    project, legacy_flag, rest = _parse_run_args(argv)
    if legacy_flag or any(t.startswith("--task-type") or t == "--task-type" for t in argv):
        return _legacy_main(argv)
    if rest and any(t.startswith("-") for t in rest):
        return _legacy_main(argv)

    return run_project(project)


if __name__ == "__main__":
    raise SystemExit(main())
