from kante.types import Info
import strawberry
from karakter import types, models, managers
import logging

from api.management.authz import assert_owner

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
    """Update an organization's details including name, description, slug, and avatar.

    Requires the caller to own the organization, matching `updateOrganization` on the
    management API. The `slug` is part of an organization's identity — it appears in
    URLs and in token `active_org` claims — so letting any authenticated principal
    rewrite it (or rename any tenant) would be a cross-tenant defacement.
    """
    organization = models.Organization.objects.filter(pk=input.id).first()
    assert_owner(info, organization)

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
    user = info.context.request.user

    organization = models.Organization.objects.create(
        slug=create_random_slug(input.name),
        name=input.name,
        description=input.description,
        owner=user,
    )
    logger.info(f"Created Organization: {organization.id} with name: {organization.name}")

    managers.create_default_roles_for_org(organization)
    managers.add_user_roles(
        user=user,
        organization=organization,
        roles=["admin"],
    )

    # The ionscale mesh is enabled by default for every organization; clients still
    # opt in to *join* it. Guarded: a no-op when ionscale isn't configured and never
    # fails org creation. Deferred import to avoid app load-order coupling.
    from ionscale.manager import ensure_org_mesh

    ensure_org_mesh(organization)

    return organization
