from kante import Info
import strawberry
from api.management import types
from karakter import models
from fakts import models as fakts_models
from fakts import logic, builders, base_models, enums
from django.utils import timezone
from datetime import timedelta
import kante


@kante.input
class AcceptDeviceCodeInput:
    """Input for creating a single-use magic device code for an organization"""

    device_code: strawberry.ID
    composition: strawberry.ID


def accept_device_code(info: Info, input: AcceptDeviceCodeInput) -> types.ManagementClient:
    """
    Create a single-use magic invite link for an organization.

    Returns an invite with a unique token that can be shared.
    The link can only be used once and expires after the specified days.
    If no roles are specified, the 'guest' role will be assigned.
    """
    user = info.context.request.user
    device_code = fakts_models.DeviceCode.objects.get(id=input.device_code)
    composition = fakts_models.Composition.objects.get(id=input.composition)
    organization = composition.organization

    validate_device_code = logic.validate_device_code(
        device_code=device_code,
        user=user,
        organization=organization,
        composition=composition,
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
        invite = models.Invite.objects.get(token=input.token)
    except models.Invite.DoesNotExist:
        raise Exception("Invalid invite token")

    # Check if invite is still pending
    if invite.status != models.Invite.Status.PENDING:
        raise Exception(f"This invite has already been {invite.status}")

    user = info.context.request.user
    invite.decline(user)

    return invite
