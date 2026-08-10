from kante import Info
import strawberry
from django.db import transaction
from api.management import types
import kante
from fakts import models as fakts_models
from ionscale.repo import get_ionscale_repo
from ionscale.manager import sync, ensure_org_mesh, apply_dns_config
from karakter import models as karakter_models
from api.management.authz import DENIED, assert_member, assert_owner_or_admin
from graphql import GraphQLError


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
    try:
        organization = fakts_models.Organization.objects.get(id=input.organization_id)
    except fakts_models.Organization.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_owner_or_admin(info, organization)

    layer = ensure_org_mesh(organization)
    if layer is None:
        raise Exception(
            "Could not enable the mesh: ionscale is not configured on this deployment."
        )
    return layer


@kante.input
class UpdateIonscaleLayerInput:
    """Input for updating an organization's mesh (ionscale layer)."""
    id: strawberry.ID = strawberry.field(description="The ID of the Ionscale layer to update.")
    name: str | None = strawberry.field(default=None, description="The name of the tailnet layer.")
    description: str | None = strawberry.field(default=None, description="The description of the tailnet layer.")
    blocked_for: list[strawberry.ID] | None = strawberry.field(default=None, description="List of membership IDs to block from accessing this layer.")
    magic_dns: bool | None = strawberry.field(default=None, description="Enable or disable MagicDNS for this mesh.")
    https_certs: bool | None = strawberry.field(default=None, description="Enable or disable HTTPS certificates for this mesh. Requires MagicDNS.")


def update_ionscale_layer(info: Info, input: UpdateIonscaleLayerInput) -> types.ManagementLayer:
    """Update an organization's mesh: member blocking and/or DNS (MagicDNS/HTTPS)."""

    try:
        layer = fakts_models.IonscaleLayer.objects.get(id=input.id)
    except fakts_models.IonscaleLayer.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, layer.organization)

    if input.blocked_for is not None:
        # Scope to this layer's organization: unscoped ids would let a member of
        # one tenant attach another tenant's memberships to their mesh.
        memberships = karakter_models.Membership.objects.filter(
            id__in=input.blocked_for, organization=layer.organization
        )
        layer.blocked_for.set(memberships)
        layer.save()
        sync(layer)

    if input.magic_dns is not None or input.https_certs is not None:
        if input.magic_dns is not None:
            layer.magic_dns_enabled = input.magic_dns
        if input.https_certs is not None:
            layer.https_enabled = input.https_certs
        # HTTPS certs require MagicDNS (the cert domain *is* the MagicDNS name).
        if layer.https_enabled and not layer.magic_dns_enabled:
            raise ValueError("HTTPS certificates require MagicDNS to be enabled.")
        # Save + push atomically: if ionscale rejects the change the model save is
        # rolled back, so the stored "desired state" never drifts ahead of what
        # ionscale actually has. Explicit user action, so the failure propagates
        # (and the UI shows an error) instead of silently reporting success.
        with transaction.atomic():
            layer.save()
            apply_dns_config(layer, raise_on_error=True)

    return layer



@kante.input
class DeleteIonscaleLayerInput:
    """Input for accepting an organization invite"""

    id: strawberry.ID


def delete_ionscale_layer(info: Info, input: DeleteIonscaleLayerInput) -> strawberry.ID:
    """Disable (delete) an organization's mesh layer.

    This previously looked up an ``InstanceAlias`` by the given id and deleted
    that instead of the layer, so "disable mesh" destroyed an unrelated routing
    entry -- and did so for any id, in any organization.

    Note: this removes the layer record only. There is no ionscale-side teardown
    helper, so the tailnet itself is left in place.
    """
    try:
        layer = fakts_models.IonscaleLayer.objects.get(id=input.id)
    except fakts_models.IonscaleLayer.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_owner_or_admin(info, layer.organization)

    layer.delete()

    return input.id


@kante.input
class CreateIonscaleAuthKeyInput:
    """Input for creating an auth key for an Ionscale layer"""
    layer_id: strawberry.ID = strawberry.field(description="The ID of the Ionscale layer to create the key for.")
    ephemeral: bool = strawberry.field(default=True, description="When enabled, machines authenticated by this key will be automatically removed after going offline.")
    tags: list[str] | None = strawberry.field(default=None, description="Machines authenticated by this key will be automatically tagged with these tags.")


def create_ionscale_auth_key(info: Info, input: CreateIonscaleAuthKeyInput) -> types.ManagementIonscaleAuthKey:
    """ """
    try:
        layer = fakts_models.IonscaleLayer.objects.get(id=input.layer_id)
    except fakts_models.IonscaleLayer.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, layer.organization)

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
