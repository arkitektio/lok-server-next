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
class AcceptCompositionDeviceCodeInput:
    """Input for creating a single-use magic device code for an organization"""

    device_code: strawberry.ID
    organization: strawberry.ID
    allow_ionscale: bool = True


def accept_composition_device_code(info: Info, input: AcceptCompositionDeviceCodeInput) -> types.ManagementComposition:
    """
    Create a single-use magic invite link for an organization.

    Returns an invite with a unique token that can be shared.
    The link can only be used once and expires after the specified days.
    If no roles are specified, the 'guest' role will be assigned.
    """
    user = info.context.request.user
    device_code = fakts_models.CompositionDeviceCode.objects.get(id=input.device_code)
    organization = models.Organization.objects.get(id=input.organization)

    manifest = device_code.manifest_as_model

    composition = fakts_models.Composition.objects.create(
        name=manifest.identifier,
        description=manifest.description or "",
        organization=organization,
        creator=user,
    )

    for servicer in manifest.instances:
        service_manifest = servicer.manifest
        device_id = service_manifest.node_id
        if device_id:
            device, _ = fakts_models.ComputeNode.objects.get_or_create(organization=organization, node_id=device_id)
        else:
            device = None
        instance = fakts_models.ServiceInstance.objects.filter(
            release__service__identifier=service_manifest.identifier,
            release__version=service_manifest.version,
            device=device,
            steward=user,
            composition=composition,
            organization=organization,
            instance_id=service_manifest.instance_id,
        ).first()

        if not instance:
            token = logic.create_api_token()
            service, _ = fakts_models.Service.objects.get_or_create(identifier=service_manifest.identifier, defaults={"description": service_manifest.description or ""})
            release, _ = fakts_models.ServiceRelease.objects.get_or_create(
                service=service,
                version=service_manifest.version,
            )
            instance = fakts_models.ServiceInstance.objects.create(
                release=release,
                device=device,
                steward=user,
                token=token,
                composition=composition,
                instance_id=service_manifest.instance_id,
                organization=organization,
            )

        for role in service_manifest.roles or []:
            r, _ = models.Role.objects.get_or_create(
                identifier=role.key,
                organization=organization,
                defaults={
                    "description": role.description or "",
                    "creating_instance": instance,
                },
            )

            r.used_by.add(instance)

        for scope in service_manifest.scopes or []:
            sc, _ = models.Scope.objects.get_or_create(
                identifier=scope.key,
                organization=organization,
                defaults={
                    "description": scope.description or "",
                    "creating_instance": instance,
                },
            )

            sc.used_by.add(instance)

        for alias in servicer.aliases:
            fakts_models.InstanceAlias.objects.update_or_create(instance=instance, host=alias.host, port=alias.port, ssl=alias.ssl, path=alias.path, kind=alias.kind, scope=alias.scope)

    for clr in manifest.clients:
        user = info.context.request.user
        client_manifest = clr.manifest

        config = base_models.DevelopmentClientConfig(
            kind=enums.ClientKindVanilla.DEVELOPMENT.value,
            token=token,
            user=user.username,
            organization=organization.slug,
            tenant=user.username,
        )

        client = builders.create_client(
            organization=organization,
            user=user,
            config=config,
            manifest=client_manifest,
            composition=composition,
        )
        
        
    if input.allow_ionscale and manifest.request_auth_key:
        composition.auth_key = logic.create_composition_auth_key(user=info.context.request.user, composition=composition)
        composition.save()
        
        
    device_code.composition = composition
    device_code.save()

    return composition


@kante.input
class DeclineCompositionDeviceCodeInput:
    """Input for declining an organization invite"""

    device_code: strawberry.ID


def decline_composition_device_code(info: Info, input: DeclineCompositionDeviceCodeInput) -> types.ManagementCompositionDeviceCode:
    """
    Decline an invite to join an organization.

    Marks the invite as declined.
    """
    try:
        invite = fakts_models.CompositionDeviceCode.objects.get(token=input.device_code)
    except fakts_models.CompositionDeviceCode.DoesNotExist:
        raise Exception("Invalid invite token")

    invite.declined = True
    invite.save()

    return invite
