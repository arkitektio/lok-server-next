from kante.types import Info
import strawberry_django
import strawberry
from karakter import types, models, managers
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


def create_organization(info: Info, input: CreateOrganizationInput) -> types.Organization:
    """Create a new organization with the given name, slug, and description."""
    organization = models.Organization.objects.create(
        slug=create_random_slug(input.name),
        name=input.name,
        description=input.description,
    )
    logger.info(f"Created Organization: {organization.id} with name: {organization.name}")
    managers.create_default_groups_for_org(organization)
    managers.add_user_roles(
        user=info.context.request.user,
        organization=organization,
        roles=["admin"],
    )
    return organization
