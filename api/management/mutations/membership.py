import logging

import strawberry
from graphql import GraphQLError
from kante.types import Info

from karakter import models
from api.management import types
from api.management.authz import is_owner, is_owner_or_admin

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateMembershipInput:
    id: strawberry.ID
    roles: list[strawberry.ID] | None = None


def update_membership(info: Info, input: UpdateMembershipInput) -> types.ManagementMembership:
    membership = models.Membership.objects.get(pk=input.id)
    organization = membership.organization
    user = info.context.request.user

    # Only the organization's owner or an admin may change a member's roles —
    # otherwise any member could grant themselves (or anyone) admin.
    if not is_owner_or_admin(user, organization):
        raise GraphQLError("You are not allowed to manage memberships for this organization.")

    if input.roles:
        # Roles must belong to the membership's own organization; never let a role
        # id from another organization be attached.
        roles = models.Role.objects.filter(pk__in=input.roles, organization=organization)
        membership.roles.set(roles)
    membership.save()
    return membership


@strawberry.input
class DeleteMembershipInput:
    id: strawberry.ID


def delete_membership(info: Info, input: DeleteMembershipInput) -> strawberry.ID:
    """Remove a member from an organization.

    Permitted for the member themselves (leaving), and for the organization's owner
    or an admin (removing someone) — until now it was self-only, so an organization
    had no way to eject anyone.

    The owner's own membership is the one exception: an admin removing it would
    leave the organization owned by a non-member, and is a step towards taking it
    over. Owners may still leave of their own accord.
    """
    membership = models.Membership.objects.get(pk=input.id)
    organization = membership.organization
    user = info.context.request.user

    is_self = membership.user_id == user.id
    if not is_self and not is_owner_or_admin(user, organization):
        raise GraphQLError("You are not allowed to manage memberships for this organization.")

    if not is_self and is_owner(membership.user, organization):
        raise GraphQLError(
            "The organization's owner cannot be removed. Transfer ownership first."
        )

    membership.delete()
    logger.info(
        "Removed user %s from organization %s (by %s)",
        membership.user_id,
        organization.slug,
        user.id,
    )
    return input.id


@strawberry.input
class SetMembershipBrandHueInput:
    organization: strawberry.ID
    brand_hue: float | None = None


def set_membership_brand_hue(
    info: Info, input: SetMembershipBrandHueInput
) -> types.ManagementMembership:
    """Set the requesting user's personal brand hue for one of their organizations.

    Scoped to the caller's own membership, so a user can only recolor their own
    view of an organization. Pass a null `brand_hue` to clear it.
    """
    membership = models.Membership.objects.get(
        user=info.context.request.user, organization_id=input.organization
    )
    membership.brand_hue = input.brand_hue
    membership.save()
    return membership
