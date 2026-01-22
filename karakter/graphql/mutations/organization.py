from kante.types import Info
import strawberry_django
import strawberry
from karakter import types, models, managers
from fakts.models import KommunityPartner
from fakts.logic import create_composition_from_partner
import logging

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateOrganizationInput:
    id: strawberry.ID
    name: str | None = None
    description: str | None = None
    avatar: strawberry.ID | None = None
    slug: str | None = None


def create_random_slug(name: str) -> str:
    """Generate a random slug based on the organization name."""
    import random
    import string

    base_slug = name.lower().replace(" ", "-")
    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{base_slug}-{random_suffix}"


def update_organization(info: Info, input: UpdateOrganizationInput) -> types.Organization:
    """Update an organization's details including name, description, slug, and avatar."""
    organization = models.Organization.objects.get(pk=input.id)

    if input.name is not None:
        organization.name = input.name

    if input.description is not None:
        organization.description = input.description

    if input.slug is not None:
        organization.slug = input.slug

    if input.avatar is not None:
        organization.avatar = models.MediaStore.objects.get(pk=input.avatar)

    organization.save()
    logger.info(f"Updated Organization: {organization.id} with name: {organization.name}")
    return organization


@strawberry.input
class CreateOrganizationInput:
    name: str
    description: str | None = None
    setup_kommunity_partners: bool = True


def auto_configure_kommunity_partners(
    organization: models.Organization,
    user: models.User,
) -> list[str]:
    """
    Scan kommunity partners and auto-configure those that apply to the user.
    
    Returns a list of partner identifiers that were applied.
    """
    applied_partners = []
    
    # Find auto-configure partners that apply to this user
    auto_configure_partners = KommunityPartner.objects.filter(auto_configure=True)
    
    for partner in auto_configure_partners:
        # Check if this partner applies to the user based on filter conditions
        if not partner.applies_to_user(user):
            logger.debug(f"Partner '{partner.identifier}' does not apply to user '{user.username}'")
            continue
        
        # Check if partner has a preconfigured composition
        if not partner.preconfigured_composition:
            logger.debug(f"Partner '{partner.identifier}' has no preconfigured composition")
            continue
        
        logger.info(f"Applying auto-configure partner '{partner.identifier}' to org '{organization.slug}'")
        
        try:
            create_composition_from_partner(
                partner=partner,
                organization=organization,
                creator=user,
                log=lambda msg: logger.info(f"  {msg}"),
            )
            applied_partners.append(partner.identifier)
        except Exception as e:
            logger.error(f"Failed to apply partner '{partner.identifier}': {e}")
    
    return applied_partners


def create_organization(info: Info, input: CreateOrganizationInput) -> types.Organization:
    """Create a new organization with the given name, slug, and description.
    
    If setup_kommunity_partners is True (default), automatically configure
    kommunity partners that apply to the creating user based on their filter conditions.
    """
    user = info.context.request.user
    
    organization = models.Organization.objects.create(
        slug=create_random_slug(input.name),
        name=input.name,
        description=input.description,
        owner=user,
    )
    logger.info(f"Created Organization: {organization.id} with name: {organization.name}")
    
    # Create default roles and add creator as admin
    managers.create_default_roles_for_org(organization)
    managers.add_user_roles(
        user=user,
        organization=organization,
        roles=["admin"],
    )
    
    # Auto-configure kommunity partners if requested
    if input.setup_kommunity_partners:
        applied_partners = auto_configure_kommunity_partners(organization, user)
        if applied_partners:
            logger.info(f"Applied {len(applied_partners)} kommunity partners to org '{organization.slug}': {applied_partners}")
    
    return organization
