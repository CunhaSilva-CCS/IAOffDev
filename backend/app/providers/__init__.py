"""Provedores locais de IA offline para desenvolvimento."""

from .registry import discover_providers, flatten_models, pick_council_models, resolve_model_ref

__all__ = [
    "discover_providers",
    "flatten_models",
    "pick_council_models",
    "resolve_model_ref",
]
