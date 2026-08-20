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
from django.conf import settings
from joserfc.jwk import RSAKey


# Generate a JWK representation from the private key. We expose the
# public part (is_private=False) as the published JWK set.
jwk = RSAKey.import_key(settings.PUBLIC_KEY)
jwk_dict = jwk.as_dict(private=False, kid=settings.KEY_ID, use="sig")  # published JWKS — public key only

@csrf_exempt
def jwks(request: HttpRequest) -> JsonResponse:
    """EXPOSE JWKS."""
    return JsonResponse({"keys": [jwk_dict]})


@csrf_exempt
@resource_protector("profile")
def user_info(request: HttpRequest) -> JsonResponse:
    from fakts.models import Client
    from authapp.oidc_claims import resolve_email, resolve_sub

    membership = request.oauth_token.user  # type: ignore

    # Recover the per-client `sub`/`email` policy from the token's client. The
    # `sub` here MUST match the id_token's `sub` for the same client (OIDC Core
    # §5.3.2), so it is resolved identically to grants.OpenIDCode.
    try:
        client = Client.objects.get(client_id=request.oauth_token.client_id)  # type: ignore
        membership_is_subject = client.membership_is_subject
        email_template = client.email_template
    except Client.DoesNotExist:
        membership_is_subject = False
        email_template = None

    return JsonResponse(
        {
            "sub": resolve_sub(membership, membership_is_subject),
            "name": membership.user.username,
            "nickname": membership.user.username,
            "preferred_username": membership.user.username,
            "email": resolve_email(membership, email_template),
            "roles": [role.identifier for role in membership.roles.all()],
            "scope": "scope",
            "active_org": membership.organization.slug,
        }
    )


def _authorization_server_metadata(request: HttpRequest) -> dict:
    """The RFC 8414 authorization-server metadata core, shared by
    /.well-known/oauth-authorization-server and /.well-known/openid-configuration
    (which adds its OIDC-specific fields on top). /.well-known/fakts inlines the
    same core so fakts clients need a single discovery request."""
    from authapp.server import GRANT_TYPES_SUPPORTED, TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED

    return {
        "issuer": settings.OIDC_ISSUER,
        "authorization_endpoint": request.build_absolute_uri(reverse("authorize")),
        "token_endpoint": request.build_absolute_uri(reverse("token")),
        "jwks_uri": request.build_absolute_uri(reverse("jwks")),
        "response_types_supported": ["code"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED,
        "grant_types_supported": GRANT_TYPES_SUPPORTED,
        "code_challenge_methods_supported": ["S256"],
        "revocation_endpoint": request.build_absolute_uri(reverse("revoke")),
        "revocation_endpoint_auth_methods_supported": TOKEN_ENDPOINT_AUTH_METHODS_SUPPORTED,
        # RFC 8628 device authorization endpoint, named "app authorization"
        # here. Non-standard in one respect: it also performs dynamic client
        # registration (the manifest in the request mints a public client
        # alongside the device code).
        "device_authorization_endpoint": request.build_absolute_uri(reverse("app_authorization")),
    }


@csrf_exempt
def oauth_authorization_server(request: HttpRequest) -> JsonResponse:
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)."""
    return JsonResponse(_authorization_server_metadata(request))


@csrf_exempt
def open_id_configuration(request: HttpRequest) -> JsonResponse:
    """OpenID Configuration: the RFC 8414 core plus the OIDC-specific fields."""
    metadata = _authorization_server_metadata(request)
    metadata.update(
        {
            "userinfo_endpoint": request.build_absolute_uri(reverse("user_info")),
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
        }
    )
    return JsonResponse(metadata)


@require_http_methods(["GET", "POST"])
def authorize(request: HttpRequest) -> HttpResponse:
    """The OAuth2/OIDC authorization endpoint.

    ``GET`` (the entry point relying parties redirect the browser to): when a
    session exists, validate the request via authlib and forward to the kontrol
    consent page (which renders the client, scopes and an organization picker);
    without a session, forward too — the SPA gates on login and returns here.

    ``POST`` (the consent decision, session-authenticated and CSRF-protected —
    the kontrol page submits a real form so the browser follows the resulting
    302 to the relying party): carries the original authorize parameters plus
    ``organization`` (slug) and ``allow``. The granted subject is the user's
    *membership* in that organization, so every code — like every token — is
    org-scoped at the database level.
    """
    from karakter.models import Membership

    if request.method == "GET":
        if request.user.is_authenticated:
            # Fail fast on an invalid request (unknown client, bad redirect_uri,
            # missing PKCE for a public client) before bouncing the user to the
            # consent UI.
            try:
                server.get_consent_grant(request=request, end_user=None)
            except OAuth2Error as error:
                return server.handle_response(*error())
        query = request.GET.urlencode()
        return redirect(f"{settings.KONTROL_FRONTEND_URL}/authorize?{query}")

    if not request.user.is_authenticated:
        return JsonResponse({"error": "login_required"}, status=401)

    if request.POST.get("allow") != "true":
        # Denied: authlib produces the standard access_denied redirect.
        return server.create_authorization_response(request, grant_user=None)

    organization = request.POST.get("organization")
    try:
        membership = Membership.objects.get(user=request.user, organization__slug=organization)
    except Membership.DoesNotExist:
        return JsonResponse(
            {"error": "invalid_request", "error_description": "You are not a member of the selected organization."},
            status=400,
        )

    return server.create_authorization_response(request, grant_user=membership)


@csrf_exempt
@require_http_methods(["POST"])
def revoke_token(request: HttpRequest) -> HttpResponse:
    """RFC 7009 token revocation endpoint (POST only).

    Sets ``OAuth2Token.revoked``, which severs the refresh chain immediately;
    the short-lived JWT access token ages out on its own.
    """
    try:
        return server.create_endpoint_response("revocation", request)
    except OAuth2Error as error:
        return server.handle_response(*error())


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
    from authapp.throttle import TOKEN_LIMIT_PER_MINUTE, is_throttled, throttled_response

    if is_throttled(request, "token", TOKEN_LIMIT_PER_MINUTE):
        return throttled_response()

    try:
        return server.create_token_response(request)
    except OAuth2Error as error:
        return server.handle_response(*error())


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
