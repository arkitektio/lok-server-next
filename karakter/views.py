from django.shortcuts import render, redirect
from allauth.socialaccount.models import SocialAccount
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

    # Get the social accounts linked to the user
    social_accounts = SocialAccount.objects.filter(user=request.user)

    context = {
        "profile_form": profile_form,
        "social_accounts": social_accounts,
    }

    return render(request, "karakter/profile.html", context)
