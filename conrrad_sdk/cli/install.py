"""conrrad install — register Citizen at gateway, persist ~/.conrrad/citizen.json"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from conrrad_sdk.pay.gateway_client import ConrradPayGateway


def install_fingerprint() -> str:
    explicit = os.environ.get("INSTALL_FINGERPRINT", "").strip()
    if explicit:
        return explicit
    sdk_version = os.environ.get("CONRRAD_SDK_VERSION", "conrrad-sdk")
    basis = f"{platform.node()}:{platform.machine()}:{sdk_version}"
    return hashlib.sha256(basis.encode()).hexdigest()


def main() -> int:
    gateway = ConrradPayGateway()
    fingerprint = install_fingerprint()
    try:
        result = gateway.register_citizen(
            developer_id=os.environ.get("DEVELOPER_ID", f"install-{platform.node()}"),
            install_fingerprint=fingerprint,
            sdk_version=os.environ.get("CONRRAD_SDK_VERSION", "conrrad-sdk"),
            hostname=platform.node(),
            capabilities=["telemetry"],
        )
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}, indent=2), file=sys.stderr)
        return 1

    citizen_id = result.get("citizenId")
    if not citizen_id:
        print(json.dumps({"success": False, "error": "register failed", "payload": result}, indent=2), file=sys.stderr)
        return 1

    creds_path = Path(os.environ.get("CONRRAD_CITIZEN_CREDS", Path.home() / ".conrrad" / "citizen.json"))
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds = {
        "citizenId": citizen_id,
        "installToken": result.get("installToken"),
        "installFingerprint": fingerprint,
        "walletId": result.get("walletId"),
        "gatewayUrl": gateway.base_url,
        "registeredAt": result.get("registeredAt"),
        "reRegistered": result.get("reRegistered"),
    }
    creds_path.write_text(json.dumps(creds, indent=2) + "\n", encoding="utf-8")
    os.chmod(creds_path, 0o600)

    print(json.dumps({"success": True, "citizenId": citizen_id, "credsPath": str(creds_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
