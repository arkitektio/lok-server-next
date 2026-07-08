from kante.types import Info
import strawberry
from api.management import types
from karakter import models, managers
from karakter import slugs
import logging
from django.db import IntegrityError
from fakts import models as fakts_models
from fakts.logic import create_hub_from_partner

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateOrganizationInput:
    id: strawberry.ID
    name: str | None = None
    description: str | None = None
    avatar: strawberry.ID | None = None
    slug: str | None = None
    brand_hue: float | None = None
    require_device_auth: bool | None = None
    sync_mine: bool = False


def update_organization(info: Info, input: UpdateOrganizationInput) -> types.ManagementOrganization:
    """Update an organization's details including name, description, slug, and avatar.

    Only the organization owner may change these org-wide settings (including the
    default brand hue).
    """
    organization = models.Organization.objects.get(pk=input.id)
    assert organization.owner == info.context.request.user, "You must own the organization to update it."

    if input.name is not None:
        organization.name = input.name

    if input.description is not None:
        organization.description = input.description

    if input.slug is not None:
        candidate = slugs.normalize_slug(input.slug)
        slugs.validate_slug(candidate)
        if candidate != organization.slug:
            assert not slugs.is_slug_taken(candidate), (
                f"The handle '{candidate}' is already taken. Try '{slugs.suggest_slug(candidate)}'."
            )
        organization.slug = candidate

    if input.avatar is not None:
        organization.avatar = models.MediaStore.objects.get(pk=input.avatar)

    if input.brand_hue is not None:
        organization.brand_hue = input.brand_hue

    if input.require_device_auth is not None:
        organization.require_device_auth = input.require_device_auth

    organization.save()

    # sync_mine: also copy the new default hue onto the owner's own membership, so
    # the owner's personal colour matches the org default they just set. Snapshots
    # the value (does not make the membership permanently follow the default).
    if input.sync_mine and input.brand_hue is not None:
        membership, _ = models.Membership.objects.get_or_create(
            user=info.context.request.user, organization=organization
        )
        membership.brand_hue = input.brand_hue
        membership.save(update_fields=["brand_hue"])

    logger.info(f"Updated Organization: {organization.id} with name: {organization.name}")
    return organization


@strawberry.input
class CreateOrganizationInput:
    name: str
    description: str | None = None
    brand_hue: float | None = None
    slug: str | None = None


def create_organization(info: Info, input: CreateOrganizationInput) -> types.ManagementOrganization:
    """Create a new organization with the given name, slug, and description.

    When no slug is supplied it is derived cleanly from the name (lowercased,
    hyphenated, no random suffix). The slug is heavily validated and must be
    unique; a taken slug is rejected with a suggested alternative.
    """
    # Prefer an explicit (user-chosen) slug, otherwise derive one from the name.
    candidate = slugs.normalize_slug(input.slug) if input.slug else slugs.slugify_name(input.name)
    slugs.validate_slug(candidate)
    assert not slugs.is_slug_taken(candidate), (
        f"The handle '{candidate}' is already taken. Try '{slugs.suggest_slug(candidate)}'."
    )

    try:
        organization = models.Organization.objects.create(
            slug=candidate,
            name=input.name,
            description=input.description,
            brand_hue=input.brand_hue,
            owner=info.context.request.user,
        )
    except IntegrityError:
        # Closes the check->create race: another org grabbed the slug in between.
        raise AssertionError(
            f"The handle '{candidate}' is already taken. Try '{slugs.suggest_slug(candidate)}'."
        )
    logger.info(f"Created Organization: {organization.id} with name: {organization.name}")
    managers.create_default_roles_for_org(organization)
    managers.add_user_roles(
        user=info.context.request.user,
        organization=organization,
        roles=["admin"],
    )

    # Provision the organization's mesh up front when enabled (IONSCALE_AUTO_CREATE_MESH).
    # ensure_org_mesh is idempotent and degrades gracefully if ionscale isn't
    # configured, so a failed/misconfigured mesh never breaks org creation.
    from django.conf import settings as django_settings

    if getattr(django_settings, "IONSCALE_AUTO_CREATE_MESH", False):
        from ionscale.manager import ensure_org_mesh

        ensure_org_mesh(organization)

    return organization


def change_organization_owner(info: Info, organization_id: strawberry.ID, new_owner_id: strawberry.ID) -> types.ManagementOrganization:
    """Change the owner of an organization to a new user.

    Args:
        info (Info): The GraphQL request info.
        organization_id (strawberry.ID): The ID of the organization to change ownership of.
        new_owner_id (strawberry.ID): The ID of the new owner user.

    Returns:
        types.ManagementOrganization: The updated organization with the new owner.
    """
    organization = models.Organization.objects.get(id=organization_id)
    new_owner = models.AbstractUser.objects.get(id=new_owner_id)

    organization.owner = new_owner
    organization.save()

    logger.info(f"Changed owner of Organization: {organization.id} to User: {new_owner.id}")
    return organization


@strawberry.input
class DeleteOrganizationInput:
    id: strawberry.ID


def delete_organization(info: Info, input: DeleteOrganizationInput) -> strawberry.ID:
    """Delete an organization by its ID."""
    organization = models.Organization.objects.get(pk=input.id)
    assert organization.owner == info.context.request.user, "Only the organization owner can delete the organization."
    organization.delete()
    logger.info(f"Deleted Organization: {organization.id}")
    return input.id


@strawberry.input
class ConnectKommunityPartnerInput:
    partner_id: strawberry.ID
    organization_id: strawberry.ID
    license_signature: str | None = None


def connect_kommunity_partner(info: Info, input: ConnectKommunityPartnerInput) -> types.ManagementHub:
    """Attach a preauthorized kommunity partner hub to an organization."""
    organization = models.Organization.objects.get(pk=input.organization_id)
    partner = fakts_models.KommunityPartner.objects.get(pk=input.partner_id)
    user = info.context.request.user

    can_manage_organization = organization.owner_id == user.id or organization.memberships.filter(
        user=user,
        roles__identifier="admin",
    ).exists()
    assert can_manage_organization, "You are not allowed to connect partners for this organization."
    assert partner.partner_kind == "preauthorized", "Only preauthorized partners can be connected directly."
    if partner.license_agreement:
        assert input.license_signature and input.license_signature.strip(), "You must sign the partner license agreement before continuing."

    hub = create_hub_from_partner(
        partner=partner,
        organization=organization,
        license_signature=input.license_signature.strip() if input.license_signature else None,
    )
    assert hub is not None, "This partner has no preconfigured hub."

    logger.info(
        "Connected kommunity partner '%s' to organization '%s' as hub '%s'",
        partner.identifier,
        organization.slug,
        hub.identifier,
    )

    return hub
