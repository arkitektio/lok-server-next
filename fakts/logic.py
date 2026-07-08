"""Backwards-compatibility shim.

The fakts business logic now lives in the :mod:`fakts.services` package, split by
responsibility (``hubs``, ``clients``, ``device_codes``, ``rendering``,
``tokens``). This module re-exports the public functions so existing imports
(``from fakts.logic import ...`` / ``logic.<fn>``) keep working. Prefer importing
from the relevant ``fakts.services.*`` module in new code.
"""

from fakts.services.clients import (
    create_client,
    create_development_client,
    validate_redeem_token,
)
from fakts.services.hubs import (
    PartnerPreAuthorizationError,
    auto_configure_kommunity_partners,
    create_hub_auth_key,
    create_hub_from_manifest,
    create_hub_from_partner,
    create_mesh_auth_key,
    run_partner_pre_authorize_hook,
)
from fakts.services.device_codes import start_mesh_device_code, validate_device_code
from fakts.services.rendering import (
    auto_compose,
    create_fake_linking_context,
    create_linking_context,
    create_serverlinking_context,
    find_instance_for_requirement_and_hub,
    render_hub,
    render_server_fakts,
)
from fakts.services.tokens import create_api_token, create_device_code, hash_requirements

__all__ = [
    "PartnerPreAuthorizationError",
    "auto_compose",
    "auto_configure_kommunity_partners",
    "create_api_token",
    "create_client",
    "create_hub_auth_key",
    "create_hub_from_manifest",
    "create_hub_from_partner",
    "create_development_client",
    "create_device_code",
    "create_mesh_auth_key",
    "create_fake_linking_context",
    "create_linking_context",
    "create_serverlinking_context",
    "find_instance_for_requirement_and_hub",
    "hash_requirements",
    "render_hub",
    "render_server_fakts",
    "run_partner_pre_authorize_hook",
    "start_mesh_device_code",
    "validate_device_code",
    "validate_redeem_token",
]
