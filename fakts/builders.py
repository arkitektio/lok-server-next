"""Backwards-compatibility shim.

The client-building logic now lives in :mod:`fakts.services.clients`. This module
re-exports it so existing imports (``from fakts.builders import create_client``)
keep working. Prefer importing from ``fakts.services.clients`` in new code.
"""

from fakts.services.clients import create_client, create_development_client

__all__ = ["create_client", "create_development_client"]
