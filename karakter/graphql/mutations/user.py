from kante import Info
import strawberry
from karakter import types, models
import logging
import kante
from graphql import GraphQLError

from api.management.authz import assert_owner_or_admin

logger = logging.getLogger(__name__)


@kante.input
class AddUserToOrganizationInput:
    user: strawberry.ID
    organization: strawberry.ID
    roles: list[str]


def add_user_to_organization(info: Info, input: AddUserToOrganizationInput) -> types.Membership:
    """Add a user to an organization and set their roles.

    Requires the caller to own the organization or hold its ``admin`` role — this
    mutation sets roles wholesale (including ``admin``), so it is the same
    privileged operation as ``updateMembership`` on the management API and carries
    the same bar. Without that check any authenticated principal could add anyone
    to any organization as an admin.
    """
    organization = models.Organization.objects.filter(pk=input.organization).first()
    assert_owner_or_admin(info, organization)

    membership, _ = models.Membership.objects.get_or_create(
        user_id=input.user,
        organization=organization,
    )

    roles = list(models.Role.objects.filter(identifier__in=input.roles, organization=organization))
    if len(roles) != len(set(input.roles)):
        # Don't half-apply: an unknown identifier means the caller's intent is
        # unclear, and silently dropping it could leave the member over- or
        # under-privileged relative to what was asked for.
        known = {role.identifier for role in roles}
        unknown = sorted(set(input.roles) - known)
        raise GraphQLError(f"Unknown role(s) for this organization: {', '.join(unknown)}")

    membership.roles.set(roles)
    logger.info(
        "Set roles %s for user %s in organization %s",
        sorted(role.identifier for role in roles),
        input.user,
        organization.slug,
    )
    return membership

