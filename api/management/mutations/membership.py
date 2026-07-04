import logging

import strawberry
from kante.types import Info

from karakter import models
from api.management import types

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateMembershipInput:
    id: strawberry.ID
    roles: list[strawberry.ID] | None = None


def update_membership(info: Info, input: UpdateMembershipInput) -> types.ManagementMembership:
    profile = models.Membership.objects.get(pk=input.id)
    if input.roles:
        profile.roles.set(models.Role.objects.filter(pk__in=input.roles))
    profile.save()
    return profile


@strawberry.input
class DeleteMembershipInput:
    id: strawberry.ID


def delete_membership(info: Info, input: DeleteMembershipInput) -> strawberry.ID:
    membership = models.Membership.objects.get(pk=input.id)
    assert membership.user == info.context.request.user
    membership.delete()
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
