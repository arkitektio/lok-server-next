"""Tests for the standard OAuth2/OIDC authorization endpoint (``/o/authorize/``).

The kontrol ``/authorize`` consent page drives this endpoint: relying parties
redirect the browser to ``GET /o/authorize/`` (which forwards to the consent
UI), and the consent form POSTs the decision back — the granted subject is the
user's *membership* in the chosen organization, so every code is org-scoped.
PKCE is required for public clients at token exchange.
"""

import hashlib
import base64
from urllib.parse import parse_qs, urlparse

import pytest
from django.urls import reverse

from tests import factories


def _setup():
    membership = factories.make_membership()
    # A separate OAuth2 client acting as the relying party being authorized.
    rp = factories.make_oauth2_client(membership=membership, redirect_uris="https://rp.example/callback")
    return membership.user, membership.organization, rp


def _authorize_params(rp, **extra):
    params = {
        "response_type": "code",
        "client_id": rp.client_id,
        "redirect_uri": "https://rp.example/callback",
        "scope": "openid profile",
        "state": "xyz-state",
        "nonce": "n-0S6",
    }
    params.update(extra)
    return params


@pytest.mark.django_db
def test_get_forwards_to_consent_page(client):
    user, _organization, rp = _setup()
    client.force_login(user)

    resp = client.get(reverse("authorize"), _authorize_params(rp), secure=True)

    assert resp.status_code == 302
    assert "/authorize?" in resp["Location"]
    assert f"client_id={rp.client_id}" in resp["Location"]


@pytest.mark.django_db
def test_get_with_unknown_client_errors_without_redirect(client):
    user, _organization, _rp = _setup()
    client.force_login(user)

    resp = client.get(
        reverse("authorize"),
        {"response_type": "code", "client_id": "not-registered", "redirect_uri": "https://rp.example/callback"},
        secure=True,
    )

    assert resp.status_code == 400


@pytest.mark.django_db
def test_post_consent_redirects_with_code(client):
    user, organization, rp = _setup()
    client.force_login(user)

    resp = client.post(
        reverse("authorize"),
        {**_authorize_params(rp), "allow": "true", "organization": str(organization.pk)},
        secure=True,
    )

    assert resp.status_code == 302
    parsed = urlparse(resp["Location"])
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "https://rp.example/callback"
    qs = parse_qs(parsed.query)
    assert qs["state"] == ["xyz-state"]
    assert qs["code"] and qs["code"][0]

    # The stored code is bound to the membership (org-scoped at the DB level).
    from authapp.models import AuthorizationCode

    code_row = AuthorizationCode.objects.get(code=qs["code"][0])
    assert code_row.membership.user == user
    assert code_row.membership.organization == organization


@pytest.mark.django_db
def test_post_deny_redirects_with_access_denied(client):
    user, _organization, rp = _setup()
    client.force_login(user)

    resp = client.post(reverse("authorize"), {**_authorize_params(rp), "allow": "false"}, secure=True)

    assert resp.status_code == 302
    assert "error=access_denied" in resp["Location"]


@pytest.mark.django_db
def test_post_without_membership_is_rejected(client):
    user, _organization, rp = _setup()
    client.force_login(user)

    resp = client.post(
        reverse("authorize"),
        {**_authorize_params(rp), "allow": "true", "organization": "999999"},
        secure=True,
    )

    assert resp.status_code == 400
    assert resp.json()["error"] == "invalid_request"


@pytest.mark.django_db
def test_post_refuses_an_unregistered_redirect_uri(client):
    """The end-to-end shape of the takeover: the endpoint 302s the browser to
    `redirect_uri`, so an unregistered one must never get that far."""
    user, organization, rp = _setup()
    client.force_login(user)

    resp = client.post(
        reverse("authorize"),
        {
            **_authorize_params(rp, redirect_uri="https://evil.example/steal"),
            "allow": "true",
            "organization": organization.slug,
        },
        secure=True,
    )

    # authlib refuses without redirecting to the attacker URL.
    assert resp.status_code == 400
    assert "evil.example" not in resp.get("Location", "")


def _s256(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


@pytest.mark.django_db
def test_pkce_is_required_for_public_clients(client):
    """A public client (no secret) cannot even obtain a code without a PKCE
    challenge, and cannot exchange one without the verifier."""
    membership = factories.make_membership()
    public_rp = factories.make_oauth2_client(
        membership=membership,
        client_secret="",
        token_endpoint_auth_method="none",
        redirect_uris="https://spa.example/callback",
    )
    client.force_login(membership.user)

    verifier = "a-very-long-code-verifier-string-for-pkce-testing-1234567890"
    params = {
        "response_type": "code",
        "client_id": public_rp.client_id,
        "redirect_uri": "https://spa.example/callback",
        "scope": "openid",
        "state": "s",
        "nonce": "n",
        "code_challenge": _s256(verifier),
        "code_challenge_method": "S256",
        "allow": "true",
        "organization": str(membership.organization_id),
    }
    resp = client.post(reverse("authorize"), params, secure=True)
    assert resp.status_code == 302
    code = parse_qs(urlparse(resp["Location"]).query)["code"][0]

    # Exchange without the verifier: refused (PKCE required for public clients).
    missing = client.post(
        reverse("token"),
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://spa.example/callback",
            "client_id": public_rp.client_id,
        },
        secure=True,
    )
    assert missing.status_code == 400

    # With the verifier: the code exchanges cleanly.
    ok = client.post(
        reverse("token"),
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://spa.example/callback",
            "client_id": public_rp.client_id,
            "code_verifier": verifier,
        },
        secure=True,
    )
    assert ok.status_code == 200, ok.json()
    assert ok.json()["access_token"]


@pytest.mark.django_db
def test_ensureopenid_provisions_client(settings):
    """ensureopenid creates an OAuth2Client from openid_apps with a matching
    secret and a narrowed grant surface."""
    from django.core.management import call_command
    from fakts.models import Client as OAuth2Client

    settings.ENSURED_OPENID_APPS = [
        {
            "client_id": "lok-frontend",
            "client_secret": "shared-secret-xyz",
            "redirect_uris": ["https://go.example/auth/callback"],
        }
    ]
    call_command("ensureopenid")

    client = OAuth2Client.objects.get(client_id="lok-frontend")
    assert client.client_secret == "shared-secret-xyz"
    assert "https://go.example/auth/callback" in client.redirect_uris
    assert client.grant_types == "authorization_code refresh_token"
    assert client.kind == "relying_party"
    assert client.token_endpoint_auth_method == "client_secret_post"
