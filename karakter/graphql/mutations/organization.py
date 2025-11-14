from kante.types import Info
import strawberry_django
import strawberry
from karakter import types, models
import logging

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateOrganizationInput:
    id: strawberry.ID
    name: str | None = None
    description: str | None = None
    avatar: strawberry.ID | None = None
    slug: str | None = None


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
