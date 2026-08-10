from kante import Info
import strawberry
from api.management import types
from karakter import models
from fakts import models as fakts_models
from api.management.authz import DENIED, assert_member
from graphql import GraphQLError
from fakts import logic
import kante


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
        device_code = fakts_models.DeviceCode.objects.get(id=input.device_code)
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
    """Input for declining an organization invite"""

    device_code: strawberry.ID


def decline_device_code(info: Info, input: DeclineDeviceCodeInput) -> types.ManagementDeviceCode:
    """
    Decline an invite to join an organization.

    Marks the invite as declined.
    """
    try:
        device_code = fakts_models.DeviceCode.objects.get(id=input.device_code)
    except fakts_models.DeviceCode.DoesNotExist:
        raise GraphQLError(DENIED)

    device_code.denied = True
    device_code.save()

    return device_code
