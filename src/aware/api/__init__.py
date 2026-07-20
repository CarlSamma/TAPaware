"""Aware API — integration interface for external engines."""

from aware.api.engine_hooks import AwareEngine
from aware.api.schemas import ProbeContext, ProbeRequest, SessionEndResult

__all__ = [
    "AwareEngine",
    "ProbeContext",
    "ProbeRequest",
    "SessionEndResult",
]
