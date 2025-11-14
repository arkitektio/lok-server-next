from kante import Info
import strawberry
from karakter import types, models
from django.utils import timezone
from datetime import timedelta
import kante


@kante.input
class CreateInviteInput:
    """Input for creating a single-use magic invite link for an organization"""

    organization: strawberry.ID | None
    expires_in_days: int | None = 7
    roles: list[str] | None = None  # Role identifiers to assign


def create_invite(info: Info, input: CreateInviteInput) -> types.Invite:
    """
    Create a single-use magic invite link for an organization.

    Returns an invite with a unique token that can be shared.
    The link can only be used once and expires after the specified days.
    If no roles are specified, the 'guest' role will be assigned.
    """
    if input.organization:
        organization = models.Organization.objects.get(id=input.organization)
    else:
        organization = info.context.request.organization

    # Calculate expiration date if specified
    expires_at = None
    if input.expires_in_days:
        expires_at = timezone.now() + timedelta(days=input.expires_in_days)

    invite = models.Invite.objects.create(
        created_by=info.context.request.user,
        created_for=organization,
        expires_at=expires_at,
    )

    # Assign roles
    if input.roles:
        # Add specified roles
        for role_identifier in input.roles:
            try:
                role = models.Role.objects.get(identifier=role_identifier, organization=organization)
                invite.roles.add(role)
            except models.Role.DoesNotExist:
                pass
    else:
        # Default to guest role if no roles specified
        try:
            guest_role = models.Role.objects.get(identifier="guest", organization=organization)
            invite.roles.add(guest_role)
        except models.Role.DoesNotExist:
            # No guest role exists, invite will have no roles
            pass

    return invite


@kante.input
class AcceptInviteInput:
    """Input for accepting an organization invite"""

    token: str


def accept_invite(info: Info, input: AcceptInviteInput) -> types.Membership:
    """
    Accept an invite to join an organization.

    Validates the invite token and adds the user to the organization.
    """
    try:
        invite = models.Invite.objects.get(token=input.token)
    except models.Invite.DoesNotExist:
        raise Exception("Invalid invite token")

    # Check if invite is still valid
    if not invite.is_valid():
        if invite.status == models.Invite.Status.ACCEPTED:
            raise Exception("This invite has already been accepted")
        elif invite.status == models.Invite.Status.DECLINED:
            raise Exception("This invite has been declined")
        elif invite.status == models.Invite.Status.CANCELLED:
            raise Exception("This invite has been cancelled")
        else:
            raise Exception("This invite has expired")

    user = info.context.request.user
    organization = invite.created_for

    # Check if user is already a member
    existing_membership = models.Membership.objects.filter(
        user=user,
        organization=organization,
    ).first()

    if existing_membership:
        # Mark invite as accepted but don't create duplicate membership
        invite.accept(user)
        return existing_membership

    # Create membership
    membership = models.Membership.objects.create(
        user=user,
        organization=organization,
    )

    # Assign roles from the invite
    invite_roles = invite.roles.all()
    if invite_roles.exists():
        membership.roles.set(invite_roles)
    else:
        # Fallback to guest role if invite has no roles
        try:
            guest_role = models.Role.objects.get(identifier="guest", organization=organization)
            membership.roles.add(guest_role)
        except models.Role.DoesNotExist:
            # No guest role exists, that's okay
            pass

    # Mark invite as accepted
    invite.accept(user)

    return membership


@kante.input
class DeclineInviteInput:
    """Input for declining an organization invite"""

    token: str


def decline_invite(info: Info, input: DeclineInviteInput) -> types.Invite:
    """
    Decline an invite to join an organization.

    Marks the invite as declined.
    """
    try:
        invite = models.Invite.objects.get(token=input.token)
    except models.Invite.DoesNotExist:
        raise Exception("Invalid invite token")

    # Check if invite is still pending
    if invite.status != models.Invite.Status.PENDING:
        raise Exception(f"This invite has already been {invite.status}")

    user = info.context.request.user
    invite.decline(user)

    return invite


@kante.input
class CancelInviteInput:
    """Input for cancelling an organization invite"""

    id: strawberry.ID


def cancel_invite(info: Info, input: CancelInviteInput) -> types.Invite:
    """
    Cancel an invite (only the creator can cancel).

    Marks the invite as cancelled.
    """
    try:
        invite = models.Invite.objects.get(id=input.id)
    except models.Invite.DoesNotExist:
        raise Exception("Invalid invite ID")

    # Check if user is the creator
    if invite.created_by != info.context.request.user:
        raise Exception("Only the invite creator can cancel it")

    # Check if invite is still pending
    if invite.status != models.Invite.Status.PENDING:
        raise Exception(f"Cannot cancel an invite that has been {invite.status}")

    invite.cancel()

    return invite
