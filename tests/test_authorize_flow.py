"""Tests for the OIDC authorization-consent mutation (``acceptAuthorizeCode``).

This is the backend the kontrol ``/authorize`` page calls. The test drives the
mutation exactly as the frontend does (a real organization id, a registered
client) to pin down whether an authorization failure is backend or frontend.
"""

import pytest
from types import SimpleNamespace
from asgiref.sync import sync_to_async
from urllib.parse import urlparse, parse_qs

from api.management.schema import schema
from tests import factories

ACCEPT = """
    mutation Accept($input: AcceptAuthorizeCodeInput!) {
        acceptAuthorizeCode(input: $input)
    }
"""


def _setup():
    membership = factories.make_membership()
    # A separate OAuth2 client acting as the relying party being authorized.
    rp = factories.make_oauth2_client(membership=membership, redirect_uris="https://rp.example/callback")
    return membership.user, membership.organization, rp


def _context(user):
    # The managementgraphql endpoint is served by strawberry's AsyncGraphQLView,
    # so info.context.request is the Django request and .user is the session user.
    return SimpleNamespace(request=SimpleNamespace(user=user))


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_accept_authorize_code_returns_redirect_with_code():
    user, organization, rp = await sync_to_async(_setup)()

    result = await schema.execute(
        ACCEPT,
        context_value=_context(user),
        variable_values={
            "input": {
                "organization": str(organization.id),
                "clientId": rp.client_id,
                "redirectUri": "https://rp.example/callback",
                "scope": "openid profile",
                "state": "xyz-state",
                "nonce": "n-0S6",
            }
        },
    )

    assert not result.errors, result.errors
    redirect = result.data["acceptAuthorizeCode"]

    parsed = urlparse(redirect)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "https://rp.example/callback"
    qs = parse_qs(parsed.query)
    assert qs["state"] == ["xyz-state"]
    assert qs["code"] and qs["code"][0]  # an authorization code was issued


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_unknown_client_gives_actionable_error():
    """An unregistered client_id yields a message that names it and points at
    openid_apps — not a bare DoesNotExist."""
    user, _organization, _rp = await sync_to_async(_setup)()

    result = await schema.execute(
        ACCEPT,
        context_value=_context(user),
        variable_values={
            "input": {
                "organization": str(_organization.id),
                "clientId": "not-registered",
                "redirectUri": "https://rp.example/callback",
                "scope": "openid",
                "state": "s",
            }
        },
    )

    assert result.errors
    message = result.errors[0].message
    assert "not-registered" in message and "openid_apps" in message


@pytest.mark.django_db
def test_ensureopenid_provisions_client(settings):
    """ensureopenid creates an OAuth2Client from openid_apps with a matching secret."""
    from django.core.management import call_command
    from authapp.models import OAuth2Client

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
