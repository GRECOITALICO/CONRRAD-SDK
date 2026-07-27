"""SubprocessRuntime production gate (H-07)."""
import os

import pytest

from conrrad_sdk.identity import SecurityError
from conrrad_sdk.runtime import SubprocessRuntime


def test_subprocess_forbidden_in_production():
    old = os.environ.get("CONRRAD_ENV")
    os.environ["CONRRAD_ENV"] = "production"
    try:
        with pytest.raises(SecurityError):
            SubprocessRuntime(allow_insecure_exec=True)
    finally:
        if old is None:
            os.environ.pop("CONRRAD_ENV", None)
        else:
            os.environ["CONRRAD_ENV"] = old
