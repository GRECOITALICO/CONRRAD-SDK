"""
CONRRAD SDK — Canonical Runtime Surface
========================================
Governed causal runtime for persistent cognitive systems.

    pip install conrrad-sdk

Migration guide: docs/migration/KAP_TO_CONRRAD_SDK.md
"""

from __future__ import annotations

import importlib
import os as _os
import warnings
from typing import Any

_os.environ["_CONRRAD_SDK_CANONICAL"] = "1"

from conrrad_sdk._legacy_alias import install_legacy_alias

install_legacy_alias()

__version__ = "2.0.0"
__author__ = "CONRRAD"

_KERNELL_CONFIG_SUNSET = "2026-10-01"

__all__ = [
    "__version__",
    "ConrradConfig",
    "Agent",
    "Memory",
    "ClusterNode",
    "ClusterDiscovery",
    "BountyBoard",
    "Bounty",
    "MemorySync",
    "Wallet",
    "ResourceLimits",
    "AgentPermissions",
    "AgentPassport",
    "SecurityError",
    "AgentGUI",
    "CommandCenter",
    "HardwareFingerprint",
    "TokenBudget",
    "CircuitBreaker",
    "CircuitOpenError",
    "TraceContext",
    "get_current_trace_id",
    "SLOMonitor",
    "HealthStatus",
    "SkillLoader",
    "SkillConfig",
    "estimate_tokens",
    "ToolResultPersister",
    "BaseLLMProvider",
    "OllamaProvider",
    "AnthropicProvider",
    "OpenAIProvider",
    "LLMRouter",
    "ComplexityLevel",
    "LLMMessage",
    "SubAgentManager",
    "TaskQueue",
    "LearningLoop",
    "TaskTrace",
    "EscrowEngine",
    "MerkleTree",
    "build_tx_merkle",
    "sign_tx",
    "verify_tx",
    "TransactionWAL",
    "AgentCard",
    "validate_agent_card",
    "Mandate",
    "escrow_from_mandate",
]

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "Agent": ("conrrad_sdk.agent", "Agent"),
    "Memory": ("conrrad_sdk.memory", "Memory"),
    "ClusterNode": ("conrrad_sdk.cluster", "ClusterNode"),
    "ClusterDiscovery": ("conrrad_sdk.cluster", "ClusterDiscovery"),
    "BountyBoard": ("conrrad_sdk.cluster", "BountyBoard"),
    "Bounty": ("conrrad_sdk.cluster", "Bounty"),
    "MemorySync": ("conrrad_sdk.cluster", "MemorySync"),
    "Wallet": ("conrrad_sdk.wallet", "Wallet"),
    "ConrradConfig": ("conrrad_sdk.config", "ConrradConfig"),
    "ResourceLimits": ("conrrad_sdk.sandbox", "ResourceLimits"),
    "AgentPermissions": ("conrrad_sdk.sandbox", "AgentPermissions"),
    "AgentPassport": ("conrrad_sdk.identity", "AgentPassport"),
    "SecurityError": ("conrrad_sdk.identity", "SecurityError"),
    "AgentGUI": ("conrrad_sdk.gui", "AgentGUI"),
    "CommandCenter": ("conrrad_sdk.dashboard", "CommandCenter"),
    "HardwareFingerprint": ("conrrad_sdk.telemetry", "HardwareFingerprint"),
    "TokenBudget": ("conrrad_sdk.budget", "TokenBudget"),
    "CircuitBreaker": ("conrrad_sdk.resilience", "CircuitBreaker"),
    "CircuitOpenError": ("conrrad_sdk.resilience", "CircuitOpenError"),
    "TraceContext": ("conrrad_sdk.tracing", "TraceContext"),
    "get_current_trace_id": ("conrrad_sdk.tracing", "get_current_trace_id"),
    "SLOMonitor": ("conrrad_sdk.health", "SLOMonitor"),
    "HealthStatus": ("conrrad_sdk.health", "HealthStatus"),
    "SkillLoader": ("conrrad_sdk.skill_loader", "SkillLoader"),
    "SkillConfig": ("conrrad_sdk.skill_loader", "SkillConfig"),
    "estimate_tokens": ("conrrad_sdk.token_estimator", "estimate_tokens"),
    "ToolResultPersister": ("conrrad_sdk.persister", "ToolResultPersister"),
    "BaseLLMProvider": ("conrrad_sdk.llm", "BaseLLMProvider"),
    "OllamaProvider": ("conrrad_sdk.llm", "OllamaProvider"),
    "AnthropicProvider": ("conrrad_sdk.llm", "AnthropicProvider"),
    "OpenAIProvider": ("conrrad_sdk.llm", "OpenAIProvider"),
    "LLMRouter": ("conrrad_sdk.llm", "LLMRouter"),
    "ComplexityLevel": ("conrrad_sdk.llm", "ComplexityLevel"),
    "LLMMessage": ("conrrad_sdk.llm", "LLMMessage"),
    "SubAgentManager": ("conrrad_sdk.delegation", "SubAgentManager"),
    "TaskQueue": ("conrrad_sdk.delegation", "TaskQueue"),
    "LearningLoop": ("conrrad_sdk.learning.loop", "LearningLoop"),
    "TaskTrace": ("conrrad_sdk.learning.loop", "TaskTrace"),
    "EscrowEngine": ("kap_escrow.engine", "EscrowEngine"),
    "MerkleTree": ("kap_escrow.merkle", "MerkleTree"),
    "build_tx_merkle": ("kap_escrow.merkle", "build_tx_merkle"),
    "sign_tx": ("kap_escrow.signing", "sign_tx"),
    "verify_tx": ("kap_escrow.signing", "verify_tx"),
    "TransactionWAL": ("kap_escrow.wal", "TransactionWAL"),
    "AgentCard": ("kap_escrow.a2a_compat", "AgentCard"),
    "validate_agent_card": ("kap_escrow.a2a_compat", "validate_agent_card"),
    "Mandate": ("kap_escrow.ap2_compat", "Mandate"),
    "escrow_from_mandate": ("kap_escrow.ap2_compat", "escrow_from_mandate"),
}


def __getattr__(name: str) -> Any:
    if name == "KernellConfig":
        warnings.warn(
            f"KernellConfig is deprecated; use ConrradConfig. Removal after {_KERNELL_CONFIG_SUNSET}.",
            DeprecationWarning,
            stacklevel=2,
        )
        return __getattr__("ConrradConfig")
    spec = _LAZY_EXPORTS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = spec
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
