from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.conf import settings


def get_frontend_url():
    """Get the frontend URL from settings or default."""
    return getattr(settings, 'KONTROL_FRONTEND_URL', '/')


@login_required
def organization_detail(request, slug):
    """Redirect to frontend organization page."""
    frontend_url = get_frontend_url()
    return redirect(f"{frontend_url}/organizations/{slug}")


@login_required
def change_org(request):
    """API endpoint to change the active organization."""
    from karakter.models import Organization

    if request.method == "POST":
        org_slug = request.POST.get("organization")
        try:
            organization = Organization.objects.get(slug=org_slug)
            request.user.active_organization = organization
            request.user.save()
            next_url = request.POST.get("next", get_frontend_url())
            return redirect(next_url)
        except Organization.DoesNotExist:
            return JsonResponse({"error": "Organization does not exist."}, status=404)

    # For GET requests, redirect to frontend
    frontend_url = get_frontend_url()
    return redirect(f"{frontend_url}/organizations")


@login_required
def accept_invite(request, token):
    """View for accepting an organization invite - redirects to frontend with token."""
    from karakter.models import Invite, Membership, Role

    try:
        invite = Invite.objects.get(token=token)
    except Invite.DoesNotExist:
        frontend_url = get_frontend_url()
        return redirect(f"{frontend_url}/invite/error?reason=invalid")

    # Check status and validity
    if invite.status != Invite.Status.PENDING:
        frontend_url = get_frontend_url()
        return redirect(f"{frontend_url}/invite/error?reason=already_processed")

    if not invite.is_valid():
        frontend_url = get_frontend_url()
        return redirect(f"{frontend_url}/invite/error?reason=expired")

    # Handle POST request (user accepts or declines the invite)
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "decline":
            invite.decline(request.user)
            frontend_url = get_frontend_url()
            return redirect(frontend_url)

        # Default action is accept
        # Check if already a member
        existing_membership = Membership.objects.filter(
            user=request.user,
            organization=invite.created_for,
        ).first()

        if existing_membership:
            invite.accept(request.user)
            request.user.active_organization = invite.created_for
            request.user.save()
            frontend_url = get_frontend_url()
            return redirect(frontend_url)

        # Create new membership
        membership = Membership.objects.create(
            user=request.user,
            organization=invite.created_for,
        )

        # Assign roles from the invite
        invite_roles = invite.roles.all()
        if invite_roles.exists():
            membership.roles.set(invite_roles)
        else:
            # Fallback to guest role if invite has no roles
            try:
                guest_role = Role.objects.get(identifier="guest", organization=invite.created_for)
                membership.roles.add(guest_role)
            except Role.DoesNotExist:
                pass

        # Mark invite as accepted
        invite.accept(request.user)

        # Set as active organization and redirect
        request.user.active_organization = invite.created_for
        request.user.save()

        frontend_url = get_frontend_url()
        return redirect(frontend_url)

    # For GET requests, redirect to frontend invite page
    frontend_url = get_frontend_url()
    return redirect(f"{frontend_url}/invite/{token}")


@login_required
def leave_org(request, slug):
    """API endpoint to leave an organization."""
    from karakter.models import Organization, Membership

    if request.method == "POST":
        try:
            organization = Organization.objects.get(slug=slug)
            membership = Membership.objects.get(user=request.user, organization=organization)
            membership.delete()

            # If the user was active in this org, unset it
            if request.user.active_organization == organization:
                request.user.active_organization = None
                request.user.save()

            frontend_url = get_frontend_url()
            return redirect(frontend_url)
        except (Organization.DoesNotExist, Membership.DoesNotExist):
            return JsonResponse({"error": "Organization or membership not found."}, status=404)

    return redirect("organization_detail", slug=slug)
