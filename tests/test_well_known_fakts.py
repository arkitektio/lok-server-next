"""The fakts well-known advertises an absolute `configure` endpoint.

`deployment.configure_url` may be configured as a root-relative path, an absolute
URL with a scheme, or a bare host — the well-known must always hand the client an
**absolute** URL, with the literal `{code}` placeholder preserved for the client to
substitute with the device code.
"""

import pytest
from django.test import override_settings

WELL_KNOWN = "/lok/.well-known/fakts"


@pytest.mark.django_db
@override_settings(DEPLOYMENT_CONFIGURE_URL="/configure/{code}")
def test_root_relative_configure_url_joins_base_domain(client):
    data = client.get(WELL_KNOWN).json()
    # The Django test client serves from http://testserver; the base domain is that
    # host with lok's script-name stripped.
    assert data["configure"] == "http://testserver/configure/{code}"


@pytest.mark.django_db
@override_settings(DEPLOYMENT_CONFIGURE_URL="https://go.arkitekt.live/configure/{code}")
def test_absolute_configure_url_used_verbatim(client):
    data = client.get(WELL_KNOWN).json()
    assert data["configure"] == "https://go.arkitekt.live/configure/{code}"


@pytest.mark.django_db
@override_settings(DEPLOYMENT_CONFIGURE_URL="go.arkitekt.live/configure/{code}")
def test_bare_host_configure_url_promoted_to_https(client):
    """The exact value the user configures — a host without a scheme — resolves to
    an https absolute URL rather than being treated as a relative path."""
    data = client.get(WELL_KNOWN).json()
    assert data["configure"] == "https://go.arkitekt.live/configure/{code}"


@pytest.mark.django_db
@override_settings(DEPLOYMENT_CONFIGURE_URL="https://go.arkitekt.live/configure/{code}")
def test_code_placeholder_is_preserved_literally(client):
    """`{code}` must survive verbatim — the client substitutes it, not the server."""
    data = client.get(WELL_KNOWN).json()
    assert "{code}" in data["configure"]


@pytest.mark.django_db
def test_base_fields_are_present(client):
    data = client.get(WELL_KNOWN).json()
    assert set(data) >= {"base_url", "frontend_url", "configure", "issuer", "token_endpoint", "jwks_uri"}
    # The old claim/challenge endpoints (and the pre-RFC-8414 field names) are
    # gone: the canonical grant lives on the token endpoint.
    for legacy in ("claim", "challenge_url", "device_code_start", "token_url", "jwks_url"):
        assert legacy not in data


@pytest.mark.django_db
def test_oauth_metadata_is_advertised(client):
    """The fakts well-known speaks RFC 8414 vocabulary: the app authorization
    (device authorization + dynamic registration) and token endpoints as
    absolute URLs, plus the supported grants and client auth methods."""
    data = client.get(WELL_KNOWN).json()
    assert data["device_authorization_endpoint"] == "http://testserver/lok/o/app-authorization/"
    assert data["token_endpoint"] == "http://testserver/lok/o/token/"
    assert data["jwks_uri"] == "http://testserver/lok/o/jwks/"
    assert "urn:ietf:params:oauth:grant-type:device_code" in data["grant_types_supported"]
    assert "urn:fakts:grant-type:redeem" in data["grant_types_supported"]
    assert "refresh_token" in data["grant_types_supported"]
    assert "none" in data["token_endpoint_auth_methods_supported"]


@pytest.mark.django_db
def test_oauth_authorization_server_document(client):
    """/.well-known/oauth-authorization-server (RFC 8414) serves the same core
    the openid-configuration builds on."""
    rfc8414 = client.get("/lok/.well-known/oauth-authorization-server").json()
    oidc = client.get("/lok/.well-known/openid-configuration").json()

    for key in ("issuer", "token_endpoint", "jwks_uri", "device_authorization_endpoint",
                "grant_types_supported", "token_endpoint_auth_methods_supported"):
        assert rfc8414[key] == oidc[key]

    # The OIDC-specific fields live only on openid-configuration.
    assert "userinfo_endpoint" in oidc and "userinfo_endpoint" not in rfc8414
    assert rfc8414["device_authorization_endpoint"] == "http://testserver/lok/o/app-authorization/"


@pytest.mark.django_db
@override_settings(DEPLOYMENT_HUB_CONFIGURE_URL="/hubconfigure/{code}")
def test_hub_endpoints_are_advertised(client):
    """The hub authorization, (deprecated) claim, and configure endpoints are
    advertised as absolute URLs (configure resolves the template against the
    base domain with `{code}` preserved)."""
    data = client.get(WELL_KNOWN).json()
    assert data["hub_authorization_endpoint"] == "http://testserver/lok/o/hub-authorization/"
    assert "hub_device_code_start" not in data
    assert "hub_challenge_url" not in data
    assert data["hub_claim"] == "http://testserver/lok/f/claimhub/"
    assert data["hub_configure"] == "http://testserver/hubconfigure/{code}"
