"""Runtime import alias: ``conrrad_os_sdk.*`` → ``conrrad_sdk.*`` (no on-disk legacy package)."""

from __future__ import annotations

import importlib.abc
import importlib.util
import sys

_LEGACY_PREFIX = "conrrad_os_sdk"
_CANONICAL_PREFIX = "conrrad_sdk"


class _HistoricalAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == _LEGACY_PREFIX:
            return None
        if not fullname.startswith(f"{_LEGACY_PREFIX}."):
            return None

        target_name = _CANONICAL_PREFIX + fullname[len(_LEGACY_PREFIX) :]
        target_spec = importlib.util.find_spec(target_name)
        if target_spec is None:
            return None

        return importlib.util.spec_from_loader(
            fullname,
            _HistoricalAliasLoader(fullname, target_name),
            origin=target_spec.origin,
            is_package=target_spec.submodule_search_locations is not None,
        )


class _HistoricalAliasLoader(importlib.abc.Loader):
    def __init__(self, fullname: str, target_name: str) -> None:
        self.fullname = fullname
        self.target_name = target_name

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        target = importlib.import_module(self.target_name)
        module.__dict__.update(target.__dict__)
        module.__name__ = self.fullname
        module.__package__ = (
            self.fullname.rpartition(".")[0] if "." in self.fullname else self.fullname
        )
        if getattr(target, "__path__", None) is not None:
            module.__path__ = target.__path__
        if getattr(target, "__spec__", None) is not None:
            module.__spec__ = target.__spec__
        sys.modules[self.fullname] = module


def install_legacy_alias() -> None:
    if any(isinstance(finder, _HistoricalAliasFinder) for finder in sys.meta_path):
        return
    sys.meta_path.insert(0, _HistoricalAliasFinder())
