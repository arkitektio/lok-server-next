"""The Composition -> Hub rename keeps deprecated `composition` aliases in the
management GraphQL API (and only there). Other surfaces were hard-renamed."""

import re

import pytest

from api.management.schema import schema as management_schema


def _sdl():
    return management_schema.as_str()


def test_hub_is_the_primary_management_surface():
    sdl = _sdl()
    for name in [
        "type ManagementHub",
        "ManagementHubDeviceCode",
        "hubDeviceCode",
        "acceptHubDeviceCode",
        "updateHub",
    ]:
        assert name in sdl, f"missing {name}"


def test_deprecated_composition_aliases_are_present_and_marked():
    """Every composition-named member the shim keeps must be @deprecated and resolve
    to the renamed Hub type (there is no `ManagementComposition` type anymore)."""
    sdl = _sdl()
    assert "ManagementComposition" not in sdl  # the type itself is renamed, not aliased

    expected_deprecated = {
        "compositions",
        "composition",
        "compositionDeviceCode",
        "compositionDeviceCodeByCode",
        "acceptCompositionDeviceCode",
        "declineCompositionDeviceCode",
        "updateComposition",
        "deleteComposition",
    }
    marked = set(re.findall(r"(\w*[Cc]omposition\w*)[^\n]*@deprecated", sdl))
    assert expected_deprecated <= marked, f"not deprecated: {expected_deprecated - marked}"

    # The deprecated device-code lookups resolve to the Hub type.
    assert re.search(r"compositionDeviceCodeByCode\([^)]*\): ManagementHubDeviceCode! @deprecated", sdl)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_deprecated_compositions_query_returns_same_rows_as_hubs():
    """End-to-end: the deprecated `compositions` query resolves through the same Hub
    queryset as the new `hubs` query and returns the org's hubs."""
    from asgiref.sync import sync_to_async

    from tests import factories
    from tests.conftest import build_auth_context

    def _setup():
        membership = factories.make_membership()
        request_client = factories.make_client(membership=membership)
        hub = factories.make_hub(organization=membership.organization)
        ctx = build_auth_context(membership.user, membership.organization, request_client.oauth2_client)
        ctx.request._user = membership.user
        return hub, ctx

    hub, ctx = await sync_to_async(_setup)()

    result = await management_schema.execute(
        "{ hubs { id name } compositions { id name } }", context_value=ctx
    )
    assert not result.errors, result.errors
    assert result.data["hubs"] == result.data["compositions"]
    assert str(hub.pk) in [h["id"] for h in result.data["compositions"]]
