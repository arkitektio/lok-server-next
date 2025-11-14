from django.shortcuts import render, redirect
from .forms import ProfileForm
from django.contrib.auth.decorators import login_required


@login_required
def profile(request):
    # Assuming `ProfileForm` is a form for your `Profile` model
    profile_form = ProfileForm(instance=request.user.profile)

    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if profile_form.is_valid():
            profile_form.save()
            return redirect("profile")

    context = {
        "profile_form": profile_form,
        "social_accounts": [],
    }

    return render(request, "karakter/profile.html", context)


@login_required
def home(request):
    return render(request, "account/home.html")


@login_required
def organization_detail(request, slug):
    from karakter.models import Organization

    try:
        organization = Organization.objects.get(slug=slug)
    except Organization.DoesNotExist:
        return redirect("home")

    context = {
        "organization": organization,
        "roles": organization.roles.all(),
    }

    return render(request, "karakter/organization_detail.html", context)


@login_required
def change_org(request):
    from karakter.models import Organization

    if request.method == "POST":
        print(request.POST)
        org_slug = request.POST.get("organization")
        try:
            organization = Organization.objects.get(slug=org_slug)
            request.user.active_organization = organization
            request.user.save()
            next_url = request.POST.get("next", "home")
            return redirect(next_url)
        except Organization.DoesNotExist:
            return render(request, "karakter/change_org.html", {"error": "Organization does not exist."})

    memberships = request.user.memberships.all()
    return render(request, "karakter/change_org.html", {"memberships": memberships})


@login_required
def accept_invite(request, token):
    """View for accepting an organization invite"""
    from karakter.models import Invite, Membership, Role

    try:
        invite = Invite.objects.get(token=token)
    except Invite.DoesNotExist:
        context = {
            "error": "Invalid invite token",
            "invite": None,
        }
        return render(request, "karakter/accept_invite.html", context)

    # Check status and validity
    if invite.status != Invite.Status.PENDING:
        if invite.status == Invite.Status.ACCEPTED:
            error = f"This invite has already been accepted by {invite.accepted_by.username}"
        elif invite.status == Invite.Status.DECLINED:
            error = f"This invite was declined by {invite.declined_by.username}"
        else:
            error = "This invite has been cancelled"

        context = {
            "error": error,
            "invite": invite,
        }
        return render(request, "karakter/accept_invite.html", context)

    if not invite.is_valid():
        context = {
            "error": "This invite has expired",
            "invite": invite,
        }
        return render(request, "karakter/accept_invite.html", context)

    # Handle POST request (user accepts or declines the invite)
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "decline":
            invite.decline(request.user)
            return redirect("home")

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
            return redirect("home")

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

        return redirect("home")

    # Display invite details for GET request
    context = {
        "invite": invite,
        "organization": invite.created_for,
        "error": None,
    }
    return render(request, "karakter/accept_invite.html", context)
