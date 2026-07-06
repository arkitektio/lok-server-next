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
def test_deprecated_fields_are_still_present(client):
    """The change is additive: the old (deprecated) fields remain for back-compat."""
    data = client.get(WELL_KNOWN).json()
    assert set(data) >= {"claim", "base_url", "frontend_url", "configure"}


@pytest.mark.django_db
def test_device_code_endpoints_are_advertised(client):
    """The device-code start and challenge endpoints are advertised as absolute
    URLs pointing at lok's own fakts API."""
    data = client.get(WELL_KNOWN).json()
    assert data["device_code_start"] == "http://testserver/lok/f/start/"
    assert data["challenge_url"] == "http://testserver/lok/f/challenge/"
