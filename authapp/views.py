# authapp/views.py
"""
authapp.views

Lightweight Django views used by the authentication subsystem.

Provided views:
- issue_token(request): POST-only token endpoint that delegates to the
    project's AuthorizationServer instance (see `authapp.server`).
- CustomLoginView: small LoginView subclass wired to the project's
    login template and redirect behavior.
- logout_view: convenience wrapper around django.contrib.auth.logout.
- home_view: a login-protected home page that exposes the current user
    in the template context.

These docstrings aim to make the code easier to navigate for new
contributors and to clarify security-related decorators (CSRF, allowed
methods).
"""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from authapp.server import server, resource_protector
from authlib.oauth2 import OAuth2Error
from django.views.decorators.csrf import csrf_exempt
from .token_generators import jwk_dict
from .models import OAuth2Token
from django.conf import settings


@csrf_exempt
def jwks(request: HttpRequest) -> JsonResponse:
    """EXPOSE JWKS."""
    return JsonResponse({"keys": [jwk_dict]})


@csrf_exempt
@resource_protector("profile")
def user_info(request: HttpRequest) -> JsonResponse:
    membership = request.oauth_token.user  # type: ignore
    return JsonResponse(
        {
            "sub": str(membership.user.id),
            "name": membership.user.username,
            "preferred_username": membership.user.username,
            "email": membership.user.email,
            "roles": [role.identifier for role in membership.roles.all()],
            "preferred_username": membership.user.username,
            "sub": membership.user.id,
            "scope": "scope",
            "active_org": membership.organization.slug,
        }
    )


# use ``server.create_token_response`` to handle token endpoint
@csrf_exempt
def open_id_configuration(request: HttpRequest) -> JsonResponse:
    """OpenID Configuration."""
    issuer = settings.OIDC_ISSUER
    # construct metadata
    metadata = {
        "issuer": issuer,
        "authorization_endpoint": "https://" + request.get_host() + "/authorize",
        "token_endpoint": request.build_absolute_uri(reverse("token")),
        "jwks_uri": request.build_absolute_uri(reverse("jwks")),
        "userinfo_endpoint": request.build_absolute_uri(reverse("user_info")),
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token"],
    }
    return JsonResponse(metadata)


@csrf_exempt
@require_http_methods(["POST"])  # we only allow POST for token endpoint
def issue_token(request: HttpRequest) -> HttpResponse | tuple:
    """Token endpoint (POST only).

    This view delegates the heavy lifting to the AuthorizationServer
    instance exported from :mod:`authapp.server` via
    ``server.create_token_response`` which returns a Django
    HttpResponse appropriate for RFC-compliant token responses.

    Security notes:
    - The endpoint is explicitly CSRF-exempt because OAuth token
      requests are typically made by non-browser clients.
    - Only POST requests are allowed.

    Args:
        request: Django HttpRequest containing the token request data.

    Returns:
        HttpResponse produced by the AuthorizationServer token handler.
    """
    return server.create_token_response(request)


class CustomLoginView(LoginView):
    """Login view configured for the project's tailwind-based template.

    Behavior:
    - Uses the 'login.html' template by default.
    - Redirects authenticated users away from the login page.
    - Falls back to the named URL 'home' after successful login.
    """

    template_name = "login.html"  # your Tailwind template
    redirect_authenticated_user = True  # Redirect if already logged in
    success_url = reverse_lazy("home")  # Replace 'home' with your view name

    def get_success_url(self) -> str | None:
        """Return the URL to redirect to after successful login.

        The method prefers a ``next`` redirect parameter when present and
        otherwise falls back to the configured ``success_url``.
        """
        # This uses ?next=... if present; otherwise falls back to success_url
        return self.get_redirect_url() or self.success_url


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log out the current user and redirect to the login page.

    Args:
        request: Django HttpRequest

    Returns:
        HttpResponse redirecting to the 'login' named URL.
    """
    logout(request)
    return redirect("login")


@login_required
def home_view(request: HttpRequest) -> HttpResponse:
    """Simple authenticated home page.

    Renders 'home.html' with the currently authenticated user available
    in the template context as ``user``.
    """
    return render(request, "home.html", {"user": request.user})
