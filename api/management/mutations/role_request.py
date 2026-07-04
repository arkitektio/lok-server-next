import logging

import strawberry
from kante.types import Info

from karakter import models
from api.management import types

logger = logging.getLogger(__name__)


@strawberry.input
class RequestRoleInput:
    organization: strawberry.ID
    role: strawberry.ID
    reason: str | None = None


def request_role(info: Info, input: RequestRoleInput) -> types.ManagementRoleRequest:
    """Request an additional role in one of the caller's organizations.

    Scoped to the caller's own membership (same pattern as
    set_membership_brand_hue), so a user can only request roles for organizations
    they already belong to. The role must belong to that organization, the member
    must not already hold it, and there must be no pending request for it yet.
    """
    request = info.context.request
    membership = models.Membership.objects.get(
        user=request.user, organization_id=input.organization
    )
    role = models.Role.objects.get(pk=input.role)

    if role.organization_id != membership.organization_id:
        raise Exception("That role does not belong to this organization.")
    if membership.roles.filter(pk=role.pk).exists():
        raise Exception("You already have this role.")
    if models.RoleRequest.objects.filter(
        membership=membership, role=role, status=models.RoleRequest.Status.PENDING
    ).exists():
        raise Exception("You already have a pending request for this role.")

    return models.RoleRequest.objects.create(
        membership=membership, role=role, reason=input.reason
    )


@strawberry.input
class ResolveRoleRequestInput:
    id: strawberry.ID


def approve_role_request(info: Info, input: ResolveRoleRequestInput) -> types.ManagementRoleRequest:
    """Approve a pending role request. Only the organization owner may do this.

    Approval adds the requested role to the member's membership.
    """
    role_request = models.RoleRequest.objects.get(pk=input.id)
    assert (
        role_request.membership.organization.owner == info.context.request.user
    ), "You must own the organization to approve role requests."
    role_request.approve(info.context.request.user)
    return role_request


def decline_role_request(info: Info, input: ResolveRoleRequestInput) -> types.ManagementRoleRequest:
    """Decline a pending role request. Only the organization owner may do this."""
    role_request = models.RoleRequest.objects.get(pk=input.id)
    assert (
        role_request.membership.organization.owner == info.context.request.user
    ), "You must own the organization to decline role requests."
    role_request.decline(info.context.request.user)
    return role_request


def cancel_role_request(info: Info, input: ResolveRoleRequestInput) -> strawberry.ID:
    """Withdraw one's own role request. Only the requesting member may do this."""
    role_request = models.RoleRequest.objects.get(pk=input.id)
    assert (
        role_request.membership.user == info.context.request.user
    ), "You can only cancel your own role requests."
    role_request.delete()
    return input.id
