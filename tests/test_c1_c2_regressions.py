"""Regressions for the two critical findings of the 2026-08-21 security review.

C1 — signup must never join an organization that already exists.
C2 — the main GraphQL API must reject a token not issued by, or not addressed
     to, this server.
"""

import pytest
from asgiref.sync import sync_to_async
from django.conf import settings

from authapp.extension import assert_addressed_to_lok
from authentikate.base_models import StaticToken
from authentikate.errors import InvalidJwtTokenError
from karakter.models import Membership, Organization, User


# --------------------------------------------------------------------------- #
# C1
# --------------------------------------------------------------------------- #


@pytest.mark.django_db
def test_signup_does_not_join_existing_organization():
    """The finding: `get_or_create(slug=f"{username}-org")` matched on slug alone
    and then granted `admin` outside the `if created` branch, so registering the
    username `acme` made you an admin of the pre-existing org `acme-org`.
    """
    victim_owner = User.objects.create(username="victim-owner")
    victim_org = Organization.objects.get_or_create(
        slug="acme-org", defaults={"name": "Acme", "owner": victim_owner}
    )[0]

    attacker = User.objects.create(username="acme")

    assert not Membership.objects.filter(
        user=attacker, organization=victim_org
    ).exists(), "signup joined the attacker to a pre-existing organization"

    # They still get their own org, just not the victim's.
    own = Organization.objects.filter(owner=attacker)
    assert own.exists()
    assert own.first().pk != victim_org.pk
    assert own.first().slug != "acme-org"


@pytest.mark.django_db
def test_signup_still_provisions_an_admin_org():
    user = User.objects.create(username="freshuser")
    org = Organization.objects.get(owner=user)
    membership = Membership.objects.get(user=user, organization=org)
    assert "admin" in {r.identifier for r in membership.roles.all()}


# --------------------------------------------------------------------------- #
# C2
# --------------------------------------------------------------------------- #


def _token(**overrides):
    claims = dict(
        sub="1",
        iss=settings.OIDC_ISSUER,
        aud=["lok"],
        client_id="some-client",
        active_org="1",  # org pk; see authapp.extension.read_org_claim
    )
    claims.update(overrides)
    return StaticToken(**claims)


def test_token_addressed_to_lok_is_accepted():
    assert_addressed_to_lok(_token())


def test_relying_party_token_is_rejected():
    """The finding: `get_audiences` mints `[client_id]` for a plain OIDC relying
    party — explicitly not `lok` — but the main schema never checked `aud`, so
    an RP's access token authenticated as its user.
    """
    with pytest.raises(InvalidJwtTokenError):
        assert_addressed_to_lok(_token(aud=["some-relying-party"]))


def test_token_without_audience_is_rejected():
    with pytest.raises(InvalidJwtTokenError):
        assert_addressed_to_lok(_token(aud=None))


def test_token_from_a_foreign_issuer_is_rejected():
    with pytest.raises(InvalidJwtTokenError):
        assert_addressed_to_lok(_token(iss="https://evil.example"))


# --------------------------------------------------------------------------- #
# Organization identity: pk, not slug
# --------------------------------------------------------------------------- #


def test_read_org_claim_rejects_a_token_naming_no_organization():
    from authapp.extension import read_org_claim

    with pytest.raises(InvalidJwtTokenError):
        # `StaticToken` narrows active_org to a plain `str`, so the empty
        # string is how "no organization" is expressed here.
        read_org_claim(_token(active_org=""))


def test_read_org_claim_reads_the_org_claim_off_a_real_jwt():
    """`JWTToken` is extra="ignore", so `org` is dropped from the model and has
    to be read back out of the (already signature-verified) raw payload."""
    import base64
    import json

    from authapp.extension import read_org_claim

    def _seg(obj):
        raw = base64.urlsafe_b64encode(json.dumps(obj).encode()).decode()
        return raw.rstrip("=")

    raw = f"{_seg({'alg': 'RS256'})}.{_seg({'org': '4242'})}.sig"
    token = _token(active_org="not-this-one")
    token.raw = raw

    assert read_org_claim(token) == "4242"


def _jwt_with_org(org_pk) -> str:
    """A syntactically-real JWT whose payload names `org`.

    The signature is irrelevant here: authentikate verifies it in `decode_token`
    *before* an `AuthAppExtension` ever sees the token, so this exercises the
    same payload-reading path production takes.
    """
    import base64
    import json

    def _seg(obj):
        return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")

    return f"{_seg({'alg': 'RS256'})}.{_seg({'org': str(org_pk)})}.sig"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_extension_resolves_the_organization_by_pk_from_a_real_token():
    """The production resolution path. Every other authenticated test goes
    through the static-token fallback, so without this the real-JWT branch of
    `read_org_claim` is only covered as a unit.
    """
    from asgiref.sync import sync_to_async

    from authapp.extension import AuthAppExtension

    org = await sync_to_async(Organization.objects.create)(
        slug="pk-resolution", name="PK Resolution", owner=await sync_to_async(User.objects.create)(username="pkowner")
    )

    token = _token()
    token.raw = _jwt_with_org(org.pk)

    resolved = await AuthAppExtension().aexpand_organization_from_token(token)
    assert resolved.pk == org.pk


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_extension_fails_closed_on_an_unknown_or_malformed_org():
    from authapp.extension import AuthAppExtension

    for raw in (_jwt_with_org(99999999), _jwt_with_org("not-a-pk")):
        token = _token()
        token.raw = raw
        with pytest.raises(InvalidJwtTokenError):
            await AuthAppExtension().aexpand_organization_from_token(token)
