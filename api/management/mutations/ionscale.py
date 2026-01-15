from kante import Info
import strawberry
from api.management import types, enums
from karakter import models
from django.utils import timezone
from datetime import timedelta
import kante
from fakts import models as fakts_models
from ionscale.repo import django_repo
from ionscale import base_models as ionscale_models
from ionscale import manager
from karakter import models as karakter_models


@kante.input
class CreateIonscaleLayerInput:
    """Input for creating a single-use magic invite link for an organization"""

    organization_id: strawberry.ID = strawberry.field(description="The ID of the organization to create the tailnet layer for.")
    name: str | None = strawberry.field(description="The name of the tailnet layer.")


def create_ionscale_layer(info: Info, input: CreateIonscaleLayerInput) -> types.ManagementLayer:
    """ """
    organization = fakts_models.Organization.objects.get(id=input.organization_id)

    name = input.name or "default"
    validated_name = name.strip().lower().replace(" ", "-")

    tailnet_name = f"{organization.slug or organization.pk}-{validated_name}"

    django_repo.create_tailnet(
        ionscale_models.TailnetCreate(
            name=tailnet_name,
        )
    )

    layer = fakts_models.IonscaleLayer.objects.create(
        organization=organization,
        name=name or "Default",
        kind=enums.LayerKind.IONSCALE.value,
        identifier=tailnet_name,
        tailnet_name=tailnet_name,
    )

    return layer


@kante.input
class UpdateIonscaleLayerInput:
    """Input for creating a single-use magic invite link for an organization"""
    id: strawberry.ID = strawberry.field(description="The ID of the Ionscale layer to update.")
    name: str | None = strawberry.field(description="The name of the tailnet layer.")
    description: str | None = strawberry.field(description="The description of the tailnet layer.")
    blocked_for: list[strawberry.ID] | None = strawberry.field(default=None, description="List of membership IDs to block from accessing this layer.")


def update_ionscale_layer(info: Info, input: UpdateIonscaleLayerInput) -> types.ManagementLayer:
    """ """

    layer = fakts_models.IonscaleLayer.objects.get(
        id=input.id
    )
    if input.blocked_for is not None:
        memberships = karakter_models.Membership.objects.filter(id__in=input.blocked_for)
        layer.blocked_for.set(memberships)
        layer.save()
    
    manager.sync(layer)
    
    

    return layer



@kante.input
class DeleteIonscaleLayerInput:
    """Input for accepting an organization invite"""

    id: strawberry.ID


def delete_ionscale_layer(info: Info, input: DeleteIonscaleLayerInput) -> strawberry.ID:
    """
    Accept an invite to join an organization.

    Validates the invite token and adds the user to the organization.
    """
    try:
        alias = fakts_models.InstanceAlias.objects.get(id=input.id)
    except fakts_models.InstanceAlias.DoesNotExist:
        raise Exception("Invalid alias ID")

    alias.delete()

    return input.id
