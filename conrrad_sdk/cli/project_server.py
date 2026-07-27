"""Minimal local dev runtime for Citizen Padre projects (VS-02)."""
from __future__ import annotations

import argparse
import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from conrrad_sdk.harvey.pipeline import HarveyPipeline


class _ProjectHandler(BaseHTTPRequestHandler):
    project_name: str = "project"
    manifest_id: str = "project"
    pipeline: HarveyPipeline | None = None

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "health": "PASS",
                    "project": self.project_name,
                    "manifest_id": self.manifest_id,
                    "citizen_padre": True,
                    "mode": "development",
                },
            )
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/query":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send_json(400, {"status": "error", "message": "invalid JSON body"})
            return

        question = str(payload.get("query") or payload.get("question") or "").strip()
        if not question:
            self._send_json(400, {"status": "error", "message": "missing query field"})
            return

        session_id = str(payload.get("session_id") or "default")
        if self.pipeline is None:
            self._send_json(503, {"status": "error", "message": "pipeline not initialized"})
            return

        result = self.pipeline.query(question, session_id=session_id)
        self._send_json(200, result)


def _load_project_meta(project_dir: Path) -> tuple[str, str]:
    manifest_path = project_dir / "manifest.json"
    name = project_dir.name
    manifest_id = name
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_id = str(data.get("id") or name)
        name = str(data.get("name") or manifest_id)
    return name, manifest_id


def main() -> int:
    parser = argparse.ArgumentParser(description="CONRRAD project dev runtime")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--project-dir", type=str, required=True)
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not (project_dir / "conrrad.yaml").is_file():
        print(f"❌ Missing conrrad.yaml in {project_dir}", file=sys.stderr)
        return 2

    project_name, manifest_id = _load_project_meta(project_dir)
    workspace = project_dir / "workspace"
    workspace.mkdir(exist_ok=True)
    log_file = workspace / "runtime.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stderr)],
        force=True,
    )

    pipeline = HarveyPipeline(workspace)

    handler = type(
        "BoundHandler",
        (_ProjectHandler,),
        {
            "project_name": project_name,
            "manifest_id": manifest_id,
            "pipeline": pipeline,
        },
    )
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
