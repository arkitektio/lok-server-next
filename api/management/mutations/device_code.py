from kante import Info
import strawberry
from api.management import types
from karakter import models
from fakts import models as fakts_models
from api.management.authz import DENIED, assert_member
from graphql import GraphQLError
from fakts import logic
import kante
from api.management.device_code_authz import resolve_declinable_device_code


@kante.input
class AcceptDeviceCodeInput:
    """Input for creating a single-use magic device code for an organization"""

    device_code: strawberry.ID
    hub: strawberry.ID
    device_name: str | None = strawberry.field(default=None, description="Name to give a newly created device (ignored if the device already exists).")
    declined_requirements: list[str] = strawberry.field(default_factory=list)
    """Requirement keys the user has explicitly declined (optional requirements only)."""


def accept_device_code(info: Info, input: AcceptDeviceCodeInput) -> types.ManagementClient:
    """
    Create a single-use magic invite link for an organization.

    Returns an invite with a unique token that can be shared.
    The link can only be used once and expires after the specified days.
    If no roles are specified, the 'guest' role will be assigned.
    """
    user = info.context.request.user
    try:
        device_code = fakts_models.DeviceCode.objects.get(id=input.device_code, kind="app")
        hub = fakts_models.Hub.objects.get(id=input.hub)
    except (fakts_models.DeviceCode.DoesNotExist, fakts_models.Hub.DoesNotExist):
        raise GraphQLError(DENIED)

    organization = hub.organization
    # Accepting mints a client and an API token inside `organization`, so the
    # caller must belong to it -- otherwise any authenticated user could name
    # another tenant's hub and provision credentials there.
    assert_member(info, organization)

    validate_device_code = logic.validate_device_code(
        device_code=device_code,
        user=user,
        organization=organization,
        hub=hub,
        device_name=input.device_name,
        declined_requirements=input.declined_requirements,
    )

    return validate_device_code.client


@kante.input
class DeclineDeviceCodeInput:
    """Input for declining a pending device code."""

    device_code: strawberry.ID
    code: str | None = strawberry.field(
        default=None,
        description="The code the device displayed. Proves the caller was actually "
        "shown this enrolment; without it, a guessed id is enough to deny "
        "someone else's. Optional only until clients are updated to send it.",
    )


def decline_device_code(info: Info, input: DeclineDeviceCodeInput) -> types.ManagementDeviceCode:
    """
    Decline an invite to join an organization.

    Marks the invite as declined.
    """
    device_code = resolve_declinable_device_code(
        fakts_models.DeviceCode, device_code_id=input.device_code, code=input.code
    )

    device_code.denied = True
    device_code.save()

    return device_code
