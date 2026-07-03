from kante import Info
import strawberry
from api.management import types
import kante
from fakts import models as fakts_models
from ionscale.repo import get_ionscale_repo
from ionscale.manager import sync, ensure_org_mesh
from karakter import models as karakter_models


@kante.input
class CreateIonscaleLayerInput:
    """Input for enabling the ionscale mesh for an organization"""

    organization_id: strawberry.ID = strawberry.field(description="The ID of the organization to enable the mesh for.")
    name: str | None = strawberry.field(description="Deprecated — the mesh is a per-organization singleton; ignored.")


def create_ionscale_layer(info: Info, input: CreateIonscaleLayerInput) -> types.ManagementLayer:
    """Enable (opt in to) the organization's ionscale mesh.

    The mesh is a per-organization singleton: if one already exists it is
    returned unchanged; otherwise it is provisioned. See `ensure_org_mesh`.
    """
    organization = fakts_models.Organization.objects.get(id=input.organization_id)

    layer = ensure_org_mesh(organization)
    if layer is None:
        raise Exception(
            "Could not enable the mesh: ionscale is not configured on this deployment."
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
    
    sync(layer)
    
    

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


@kante.input
class CreateIonscaleAuthKeyInput:
    """Input for creating an auth key for an Ionscale layer"""
    layer_id: strawberry.ID = strawberry.field(description="The ID of the Ionscale layer to create the key for.")
    ephemeral: bool = strawberry.field(default=True, description="When enabled, machines authenticated by this key will be automatically removed after going offline.")
    tags: list[str] | None = strawberry.field(default=None, description="Machines authenticated by this key will be automatically tagged with these tags.")


def create_ionscale_auth_key(info: Info, input: CreateIonscaleAuthKeyInput) -> types.ManagementIonscaleAuthKey:
    """ """
    layer = fakts_models.IonscaleLayer.objects.get(id=input.layer_id)
    if not layer.organization.memberships.filter(user=info.context.request.user).exists():
        raise PermissionError("You are not a member of the organization that owns this layer.")

    key = get_ionscale_repo().create_auth_key(
        tailnet=layer.tailnet_name,
        ephemeral=input.ephemeral,
        pre_authorized=True,
        tags=input.tags
    )

    key = fakts_models.IonscaleAuthKey.objects.create(
        layer=layer,
        key=key,
        creator=info.context.request.user,
        ephemeral=input.ephemeral,
        tags=input.tags or []
    )
    
    return key
