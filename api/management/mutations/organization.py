from kante.types import Info
import strawberry
from api.management import types
from karakter import models, managers
import logging
from fakts import models as fakts_models
from fakts.logic import create_composition_from_partner

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateOrganizationInput:
    id: strawberry.ID
    name: str | None = None
    description: str | None = None
    avatar: strawberry.ID | None = None
    slug: str | None = None
    brand_hue: float | None = None
    sync_mine: bool = False


def create_random_slug(name: str) -> str:
    """Generate a random slug based on the organization name."""
    import random
    import string

    base_slug = name.lower().replace(" ", "-")
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{base_slug}-{random_suffix}"


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
        organization.slug = input.slug

    if input.avatar is not None:
        organization.avatar = models.MediaStore.objects.get(pk=input.avatar)

    if input.brand_hue is not None:
        organization.brand_hue = input.brand_hue

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


def create_organization(info: Info, input: CreateOrganizationInput) -> types.ManagementOrganization:
    """Create a new organization with the given name, slug, and description."""
    organization = models.Organization.objects.create(
        slug=create_random_slug(input.name),
        name=input.name,
        description=input.description,
        brand_hue=input.brand_hue,
        owner=info.context.request.user,
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


def connect_kommunity_partner(info: Info, input: ConnectKommunityPartnerInput) -> types.ManagementComposition:
    """Attach a preauthorized kommunity partner composition to an organization."""
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

    composition = create_composition_from_partner(
        partner=partner,
        organization=organization,
        license_signature=input.license_signature.strip() if input.license_signature else None,
    )
    assert composition is not None, "This partner has no preconfigured composition."

    logger.info(
        "Connected kommunity partner '%s' to organization '%s' as composition '%s'",
        partner.identifier,
        organization.slug,
        composition.identifier,
    )

    return composition
