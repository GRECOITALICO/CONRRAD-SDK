"""Load citizen emit SDK without importing full conrrad_sdk (no pydantic etc.)."""
from __future__ import annotations

import sys
import types
from pathlib import Path
from importlib import util


def load_citizen_sdk(conrrad_sdk_root: Path):
    """Return Citizen class from conrrad_sdk.citizen without executing conrrad_sdk/__init__.py."""
    base = conrrad_sdk_root / "conrrad_sdk"
    if str(conrrad_sdk_root) not in sys.path:
        sys.path.insert(0, str(conrrad_sdk_root))

    def _load(name: str, rel: str):
        full = f"conrrad_sdk.{name}"
        if full in sys.modules:
            return sys.modules[full]
        path = base / rel
        spec = util.spec_from_file_location(full, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {path}")
        mod = util.module_from_spec(spec)
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
        return mod

    if "conrrad_sdk" not in sys.modules:
        pkg = types.ModuleType("conrrad_sdk")
        pkg.__path__ = [str(base)]  # type: ignore[attr-defined]
        sys.modules["conrrad_sdk"] = pkg

    for pkg_name, init_rel in (
        ("events", "events/__init__.py"),
        ("citizen", "citizen/__init__.py"),
    ):
        full = f"conrrad_sdk.{pkg_name}"
        if full not in sys.modules:
            p = types.ModuleType(full)
            p.__path__ = [str(base / pkg_name)]  # type: ignore[attr-defined]
            sys.modules[full] = p

    _load("events.idl", "events/idl.py")
    _load("events.emitter", "events/emitter.py")
    _load("citizen.home", "citizen/home.py")
    _load("citizen.fluent", "citizen/fluent.py")
    sdk = _load("citizen.sdk", "citizen/sdk.py")
    return sdk.Citizen
