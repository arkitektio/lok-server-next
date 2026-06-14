"""Tests for authapp JWT/OIDC token generation, including the client_role claim."""

import pytest
from django.conf import settings

from authapp.token_generators import MyJWTBearerTokenGenerator
from fakts.enums import ClientRoleChoices
from tests import factories


def _generator():
    return MyJWTBearerTokenGenerator(issuer=settings.OIDC_ISSUER)


@pytest.mark.django_db
def test_get_extra_claims_includes_client_role_and_org():
    membership = factories.make_membership()
    oauth2 = factories.make_oauth2_client(membership=membership)
    factories.make_client(membership=membership, oauth2_client=oauth2, role=ClientRoleChoices.AGENT.value)

    claims = _generator().get_extra_claims(oauth2, "client_credentials", membership, None)

    assert claims["client_role"] == "agent"
    assert claims["active_org"] == membership.organization.slug
    assert claims["sub"] == str(membership.user.id)
    assert claims["preferred_username"] == membership.user.username


@pytest.mark.django_db
def test_get_extra_claims_defaults_role_to_interface():
    membership = factories.make_membership()
    oauth2 = factories.make_oauth2_client(membership=membership)
    factories.make_client(membership=membership, oauth2_client=oauth2)

    claims = _generator().get_extra_claims(oauth2, "client_credentials", membership, None)
    assert claims["client_role"] == "interface"


@pytest.mark.django_db
def test_get_audiences_is_rekuest():
    membership = factories.make_membership()
    oauth2 = factories.make_oauth2_client(membership=membership)

    assert _generator().get_audiences(oauth2, membership, None) == ["rekuest"]


def test_get_jwks_exposes_signing_key():
    jwks = _generator().get_jwks()
    assert jwks["kty"] == "RSA"
    assert jwks["use"] == "sig"
    assert jwks["kid"] == "1"
    # public modulus/exponent are present so consumers can verify signatures
    assert jwks["n"] and jwks["e"]


@pytest.mark.django_db
def test_openid_user_info_contains_subject():
    from authapp.grants import OpenIDCode

    membership = factories.make_membership()
    info = OpenIDCode().generate_user_info(membership, "openid profile email")

    assert info["sub"] == str(membership.user.id)
    assert info["active_org"] == membership.organization.slug
