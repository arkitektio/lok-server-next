from kante.types import Info
import strawberry_django
import strawberry
from karakter import types, models, managers
from fakts.logic import auto_configure_kommunity_partners
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
