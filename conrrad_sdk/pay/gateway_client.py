"""
CONRRAD Pay Gateway client — citizen registration + permit verification.

Targets the remote gateway node (VPS) or local Observatory for development.
Uses stdlib urllib only (no extra dependencies).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


def _default_gateway_url() -> str:
    return (
        os.environ.get("CONRRAD_GATEWAY_URL")
        or os.environ.get("CONRRAD_PAY_GATEWAY_URL")
        or "http://127.0.0.1:23817"
    ).rstrip("/")


class ConrradPayGateway:
    """HTTP client for CONRRAD Pay + Control Plane on the gateway node."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 15.0):
        self.base_url = (base_url or _default_gateway_url()).rstrip("/")
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = None
        req_headers = {"Accept": "application/json", **(headers or {})}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"error": raw or str(e)}
            message = payload.get("error") or f"HTTP {e.code}"
            raise RuntimeError(message) from e

    def register_citizen(
        self,
        *,
        developer_id: str,
        install_fingerprint: str,
        wallet_pubkey: Optional[str] = None,
        sdk_version: Optional[str] = None,
        hostname: Optional[str] = None,
        capabilities: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Register this SDK installation as a CONRRAD citizen on the gateway."""
        return self._request(
            "POST",
            "/api/pay/citizen/register",
            {
                "developerId": developer_id,
                "installFingerprint": install_fingerprint,
                "walletPubkey": wallet_pubkey,
                "sdkVersion": sdk_version,
                "hostname": hostname,
                "capabilities": capabilities or ["telemetry"],
            },
        )

    def heartbeat(
        self,
        *,
        citizen_id: str,
        install_token: str,
        telemetry: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/api/pay/citizen/heartbeat",
            {
                "citizenId": citizen_id,
                "installToken": install_token,
                "telemetry": telemetry or {},
            },
        )

    def verify_permit(self, permit_id: str) -> Dict[str, Any]:
        """Verify an ExecutionPermit signature + expiry (no install token required)."""
        return self._request("GET", f"/api/pay/permit/{permit_id}/verify")

    def request_permit(
        self,
        *,
        citizen_id: str,
        install_token: str,
        envelope_id: str,
        budget_micro: int,
        ttl_seconds: int = 3600,
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/api/pay/permit",
            {
                "citizenId": citizen_id,
                "installToken": install_token,
                "envelopeId": envelope_id,
                "budgetMicro": budget_micro,
                "ttlSeconds": ttl_seconds,
            },
        )

    def wallet_balance(self, wallet_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/pay/wallet/{wallet_id}/balance")

    def list_control_plane_nodes(self) -> Dict[str, Any]:
        """List nodes registered on the control plane (Dell Observatory)."""
        return self._request("GET", "/api/control-plane/nodes")

    def capture_permit(
        self,
        *,
        citizen_id: str,
        install_token: str,
        permit_id: str,
        amount_micro: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Capture the held budget for a permit."""
        return self._request(
            "POST",
            "/api/pay/capture",
            {
                "citizenId": citizen_id,
                "installToken": install_token,
                "permitId": permit_id,
                "amountMicro": amount_micro,
            },
        )

    def release_permit(
        self,
        *,
        citizen_id: str,
        install_token: str,
        permit_id: str,
        amount_micro: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Release the held budget for a permit (or partial release)."""
        return self._request(
            "POST",
            "/api/pay/release",
            {
                "citizenId": citizen_id,
                "installToken": install_token,
                "permitId": permit_id,
                "amountMicro": amount_micro,
            },
        )


class ExecutionEnvelope:
    """Context manager for automating CONRRAD Pay ExecutionPermits."""

    def __init__(
        self,
        gateway: ConrradPayGateway,
        citizen_id: str,
        install_token: str,
        envelope_id: str,
        budget_micro: int,
        ttl_seconds: int = 3600,
    ):
        self.gateway = gateway
        self.citizen_id = citizen_id
        self.install_token = install_token
        self.envelope_id = envelope_id
        self.budget_micro = budget_micro
        self.ttl_seconds = ttl_seconds
        self.permit_id: Optional[str] = None
        self.permit: Optional[Dict[str, Any]] = None

    def __enter__(self):
        resp = self.gateway.request_permit(
            citizen_id=self.citizen_id,
            install_token=self.install_token,
            envelope_id=self.envelope_id,
            budget_micro=self.budget_micro,
            ttl_seconds=self.ttl_seconds,
        )
        self.permit = resp.get("permit")
        if not self.permit:
            raise RuntimeError(f"Failed to obtain permit: {resp}")
        self.permit_id = self.permit.get("permitId")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.permit_id:
            return False

        if exc_type is None:
            self.gateway.capture_permit(
                citizen_id=self.citizen_id,
                install_token=self.install_token,
                permit_id=self.permit_id,
            )
        else:
            self.gateway.release_permit(
                citizen_id=self.citizen_id,
                install_token=self.install_token,
                permit_id=self.permit_id,
            )
        return False
