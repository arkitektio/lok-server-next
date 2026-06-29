"""Small token / hashing helpers used across the fakts services."""

from hashlib import sha256
from uuid import uuid4

from fakts import base_models


def create_api_token() -> str:
    """Return a fresh opaque API token (used as a client's fakts token)."""
    return str(uuid4())


def create_device_code() -> str:
    """Return a short, human-transcribable device/challenge code."""
    return "".join([str(uuid4())[-1] for _ in range(8)])


def hash_requirements(requirements: list[base_models.Requirement]) -> str:
    """Stable hash of a manifest's requirements (order-independent)."""
    return sha256(".".join(sorted([req.service + req.key for req in requirements])).encode()).hexdigest()
