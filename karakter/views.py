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