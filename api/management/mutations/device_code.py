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
    organization: strawberry.ID


def accept_device_code(info: Info, input: AcceptDeviceCodeInput) -> types.ManagementClient:
    """
    Create a single-use magic invite link for an organization.

    Returns an invite with a unique token that can be shared.
    The link can only be used once and expires after the specified days.
    If no roles are specified, the 'guest' role will be assigned.
    """
    user = info.context.request.user
    device_code = fakts_models.DeviceCode.objects.get(id=input.device_code)
    organization = models.Organization.objects.get(id=input.organization)

    manifest = device_code.manifest_as_model

    node_id = manifest.node_id
    if node_id:
        node, _ = fakts_models.ComputeNode.objects.get_or_create(organization=organization, node_id=node_id)
    else:
        node = None

    redirect_uris = (" ".join(device_code.staging_redirect_uris),)

    client = fakts_models.Client.objects.filter(
        release__app__identifier=device_code.staging_manifest["identifier"],
        release__version=device_code.staging_manifest["version"],
        kind=device_code.staging_kind,
        node=node,
        tenant=user,
        organization=organization,
        redirect_uris=redirect_uris,
    ).first()

    if not client:
        token = logic.create_api_token()

        config = None

        if device_code.staging_kind == enums.ClientKindVanilla.DEVELOPMENT.value:
            config = base_models.DevelopmentClientConfig(
                kind=enums.ClientKindVanilla.DEVELOPMENT.value,
                token=token,
                user=user.username,
                organization=organization.slug,
                tenant=user.username,
            )

        else:
            raise Exception("Unknown client kind or no longer supported")

        client = builders.create_client(
            manifest=manifest,
            config=config,
            user=user,
            organization=organization,
        )

    device_code.client = client
    device_code.save()

    return client


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
