"""VS-06 Platform Runtime HTTP server — health · heartbeat · metrics · roadmap sync."""
from __future__ import annotations

import json
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from conrrad_sdk.runtime.state import RuntimeState, capture_integrity, verify_integrity


class PlatformRuntime:
    def __init__(
        self,
        repo_root: Path,
        citizen_id: str,
        citizen_dir: Path | None,
        runtime_dir: Path,
        *,
        sync_interval_s: float = 2.0,
    ):
        self.repo_root = repo_root.resolve()
        self.citizen_id = citizen_id
        self.citizen_dir = citizen_dir
        self.runtime_dir = runtime_dir
        self.sync_interval_s = sync_interval_s
        self.started_at = time.monotonic()
        self.state_path = runtime_dir / "state.json"
        self.log_path = runtime_dir / "runtime.jsonl"
        self.roadmap_path = runtime_dir / "roadmap_snapshot.json"
        self.integrity_start = capture_integrity(repo_root, citizen_dir)
        self.state = RuntimeState.new(citizen_id, repo_root, self.integrity_start)
        self._stop_sync = threading.Event()
        self._sync_thread: threading.Thread | None = None

    def setup_logging(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def _log_event(self, event: str, **fields: Any) -> None:
        payload = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event,
            "citizen_id": self.citizen_id,
            **fields,
        }
        line = json.dumps(payload, ensure_ascii=False) + "\n"
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(line)

    def _sync_roadmap_once(self) -> dict[str, Any]:
        services = self.repo_root / "services"
        if str(services) not in sys.path:
            sys.path.insert(0, str(services))
        from founderos.roadmap_engine import build_roadmap_view  # noqa: WPS433

        view = build_roadmap_view(self.repo_root)
        self.roadmap_path.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8")
        self._log_event("roadmap_sync", read_only=True, generated_at=view.get("generated_at"))
        return view

    def _roadmap_sync_loop(self) -> None:
        while not self._stop_sync.wait(self.sync_interval_s):
            try:
                self._sync_roadmap_once()
            except Exception as exc:
                self._log_event("roadmap_sync_error", error=str(exc))

    def start_background_sync(self) -> None:
        self._sync_roadmap_once()
        self._sync_thread = threading.Thread(target=self._roadmap_sync_loop, daemon=True)
        self._sync_thread.start()

    def stop_background_sync(self) -> None:
        self._stop_sync.set()

    def uptime_seconds(self) -> float:
        return time.monotonic() - self.started_at

    def heartbeat_payload(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.state.last_heartbeat = now
        self.state.save(self.state_path)
        return {
            "schema": "conrrad.runtime.heartbeat/v1",
            "citizen_id": self.citizen_id,
            "timestamp": now,
            "uptime_seconds": round(self.uptime_seconds(), 3),
            "restart_count": self.state.restart_count,
            "founder_artifact_id": self.integrity_start.founder_artifact_id,
        }

    def health_payload(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "conrrad-platform-runtime",
            "citizen_id": self.citizen_id,
            "uptime_seconds": round(self.uptime_seconds(), 3),
            "restart_count": self.state.restart_count,
        }

    def metrics_payload(self) -> dict[str, Any]:
        return {
            "schema": "conrrad.runtime.metrics/v1",
            "citizen_id": self.citizen_id,
            "uptime_seconds": round(self.uptime_seconds(), 3),
            "restart_count": self.state.restart_count,
            "roadmap_snapshot_bytes": self.roadmap_path.stat().st_size if self.roadmap_path.is_file() else 0,
            "log_bytes": self.log_path.stat().st_size if self.log_path.is_file() else 0,
        }

    def verify_state_consistent(self) -> tuple[bool, str]:
        current = capture_integrity(self.repo_root, self.citizen_dir)
        return verify_integrity(self.integrity_start, current)


def make_handler(runtime: PlatformRuntime):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            runtime._log_event("http_access", path=self.path, client=self.address_string())

        def _json(self, payload: dict, status: int = 200) -> None:
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path in ("/health", "/api/health"):
                self._json(runtime.health_payload())
                return
            if self.path in ("/heartbeat", "/api/heartbeat"):
                self._json(runtime.heartbeat_payload())
                return
            if self.path in ("/metrics", "/api/metrics"):
                self._json(runtime.metrics_payload())
                return
            self.send_error(404)

    return Handler


def serve(
    repo_root: Path,
    citizen_id: str,
    citizen_dir: Path | None,
    runtime_dir: Path,
    host: str,
    port: int,
) -> None:
    runtime = PlatformRuntime(repo_root, citizen_id, citizen_dir, runtime_dir)
    runtime.setup_logging()
    if runtime.state_path.is_file():
        prev = RuntimeState.load(runtime.state_path)
        runtime.state.restart_count = prev.restart_count
        runtime.state.started_at = prev.started_at
    runtime.state.pid = __import__("os").getpid()
    runtime.state.save(runtime.state_path)
    (runtime_dir / "server.pid").write_text(str(runtime.state.pid) + "\n", encoding="utf-8")
    runtime.start_background_sync()
    runtime._log_event("runtime_start", host=host, port=port)

    server = ThreadingHTTPServer((host, port), make_handler(runtime))
    try:
        server.serve_forever()
    finally:
        runtime.stop_background_sync()
        runtime._log_event("runtime_stop")
