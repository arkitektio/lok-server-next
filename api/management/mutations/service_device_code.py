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
class AcceptServiceDeviceCodeInput:
    """Input for creating a single-use magic device code for an organization"""

    device_code: strawberry.ID
    organization: strawberry.ID


def accept_service_device_code(info: Info, input: AcceptServiceDeviceCodeInput) -> types.ManagementServiceInstance:
    """
    Create a single-use magic invite link for an organization.

    Returns an invite with a unique token that can be shared.
    The link can only be used once and expires after the specified days.
    If no roles are specified, the 'guest' role will be assigned.
    """
    user = info.context.request.user
    device_code = fakts_models.ServiceDeviceCode.objects.get(id=input.device_code)
    organization = models.Organization.objects.get(id=input.organization)

    manifest = device_code.manifest_as_model
    aliases = device_code.aliases_as_models

    device_id = manifest.node_id
    if device_id:
        device, _ = fakts_models.ComputeNode.objects.get_or_create(organization=organization, node_id=device_id)
    else:
        device = None

    instance = fakts_models.ServiceInstance.objects.filter(
        release__service__identifier=manifest.identifier,
        release__version=manifest.version,
        device=device,
        steward=user,
        organization=organization,
        instance_id=manifest.instance_id,
    ).first()

    if not instance:
        token = logic.create_api_token()
        service, _ = fakts_models.Service.objects.get_or_create(identifier=manifest.identifier, defaults={"description": manifest.description or ""})
        release, _ = fakts_models.ServiceRelease.objects.get_or_create(
            service=service,
            version=manifest.version,
        )
        instance = fakts_models.ServiceInstance.objects.create(
            release=release,
            device=device,
            steward=user,
            token=token,
            instance_id=manifest.instance_id,
            organization=organization,
        )

    for role in manifest.roles or []:
        models.Role.objects.update_or_create(
            identifier=role.key,
            organization=organization,
            defaults={
                "description": role.description or "",
                "creating_instance": instance,
            },
        )

    for scope in manifest.scopes or []:
        models.Scope.objects.update_or_create(
            identifier=scope.key,
            organization=organization,
            defaults={
                "description": scope.description or "",
                "creating_instance": instance,
            },
        )

    print("Creating aliases:", aliases)
    for alias in aliases:
        fakts_models.InstanceAlias.objects.update_or_create(instance=instance, host=alias.host, port=alias.port, ssl=alias.ssl, path=alias.path, kind=alias.kind)

    device_code.instance = instance
    device_code.save()

    return instance


@kante.input
class DeclineServiceDeviceCodeInput:
    """Input for declining an organization invite"""

    device_code: strawberry.ID


def decline_service_device_code(info: Info, input: DeclineServiceDeviceCodeInput) -> types.ManagementServiceDeviceCode:
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
