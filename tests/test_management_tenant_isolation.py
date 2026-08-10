"""Cross-tenant isolation regressions for the management API.

The endpoint-wide gate in ``RequireAuthenticationExtension`` only stops anonymous
callers. These tests cover the second half of the problem: an *authenticated*
member of org A must not be able to read or mutate org B's objects by guessing
sequential ids.

Denials are asserted on the shared "Not found, or you are not authorized" text so
the error cannot be used as an existence oracle.

Setup runs through ``sync_to_async`` (matching ``test_alias_public``) because the
ORM is not usable from the event loop the async schema executes on.
"""

import pytest
from asgiref.sync import sync_to_async

from api.management.schema import schema as management_schema
from fakts import models as fakts_models
from tests import factories
from tests.conftest import build_auth_context


def _two_org_setup():
    """Two unrelated tenants plus an authenticated context for the attacker's org."""
    attacker_membership = factories.make_membership()
    request_client = factories.make_client(membership=attacker_membership)
    attacker = attacker_membership.user
    org_a = attacker_membership.organization

    victim = factories.make_user()
    org_b = factories.make_organization(owner=victim)

    context = build_auth_context(attacker, org_a, request_client.oauth2_client)
    return context, org_a, org_b, attacker, victim


def _assert_denied(result):
    assert result.errors, f"expected a denial, got data: {result.data}"
    message = result.errors[0].message
    assert "not authorized" in message or "Authentication required" in message, message


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cannot_read_other_orgs_organization():
    context, _org_a, org_b, _attacker, _victim = await sync_to_async(_two_org_setup)()

    result = await management_schema.execute(
        "query ($id: ID!) { organization(id: $id) { id slug } }",
        context_value=context,
        variable_values={"id": str(org_b.id)},
    )
    _assert_denied(result)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cannot_read_other_orgs_hub():
    context, _org_a, org_b, _attacker, _victim = await sync_to_async(_two_org_setup)()
    hub = await sync_to_async(factories.make_hub)(organization=org_b)

    result = await management_schema.execute(
        "query ($id: ID!) { hub(id: $id) { id name } }",
        context_value=context,
        variable_values={"id": str(hub.id)},
    )
    _assert_denied(result)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_can_read_own_orgs_hub():
    """The scoping must not be so tight that legitimate access breaks."""
    context, org_a, _org_b, _attacker, _victim = await sync_to_async(_two_org_setup)()
    hub = await sync_to_async(factories.make_hub)(organization=org_a)

    result = await management_schema.execute(
        "query ($id: ID!) { hub(id: $id) { id name } }",
        context_value=context,
        variable_values={"id": str(hub.id)},
    )
    assert not result.errors, result.errors
    assert result.data["hub"]["id"] == str(hub.id)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cannot_take_over_another_organization():
    """``changeOrganizationOwner`` was the full-takeover mutation."""
    context, _org_a, org_b, attacker, victim = await sync_to_async(_two_org_setup)()

    result = await management_schema.execute(
        "mutation ($org: ID!, $new: ID!) { changeOrganizationOwner(organizationId: $org, newOwnerId: $new) { id } }",
        context_value=context,
        variable_values={"org": str(org_b.id), "new": str(attacker.id)},
    )
    assert result.errors, f"takeover succeeded: {result.data}"

    owner_id = await sync_to_async(
        lambda: fakts_models.Organization.objects.get(id=org_b.id).owner_id
    )()
    assert owner_id == victim.id


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cannot_delete_another_orgs_device():
    context, _org_a, org_b, _attacker, _victim = await sync_to_async(_two_org_setup)()
    device = await sync_to_async(fakts_models.Device.objects.create)(
        organization=org_b, node_id="victim-node", name="victim"
    )

    result = await management_schema.execute(
        "mutation ($id: ID!) { deleteDevice(input: {id: $id}) }",
        context_value=context,
        variable_values={"id": str(device.id)},
    )
    _assert_denied(result)

    still_there = await sync_to_async(fakts_models.Device.objects.filter(id=device.id).exists)()
    assert still_there


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cannot_hijack_another_orgs_alias():
    """Aliases are routing entries: repointing one hijacks that service's traffic."""

    def setup():
        context, _org_a, org_b, _attacker, _victim = _two_org_setup()
        hub = factories.make_hub(organization=org_b)
        instance = factories.make_service_instance(hub=hub)
        alias = fakts_models.InstanceAlias.objects.create(
            instance=instance, host="victim.example", port=443, kind="absolute"
        )
        return context, alias

    context, alias = await sync_to_async(setup)()

    result = await management_schema.execute(
        """
        mutation ($id: ID!) {
            updateAlias(input: {id: $id, host: "attacker.example", port: 8080, kind: "absolute"}) { id host }
        }
        """,
        context_value=context,
        variable_values={"id": str(alias.id)},
    )
    _assert_denied(result)

    host = await sync_to_async(
        lambda: fakts_models.InstanceAlias.objects.get(id=alias.id).host
    )()
    assert host == "victim.example"


@pytest.mark.django_db(transaction=True)
def test_upload_key_is_namespaced_to_the_caller():
    """An attacker-chosen upload key must not address another tenant's object."""
    from api.management.mutations.upload import _scoped_key

    context, _org_a, _org_b, attacker, _victim = _two_org_setup()
    info = type("Info", (), {"context": context})()

    assert _scoped_key(info, "avatar.png") == f"users/{attacker.id}/avatar.png"
    # Traversal and absolute paths cannot escape the per-user prefix.
    assert _scoped_key(info, "../../victim/avatar.png") == f"users/{attacker.id}/avatar.png"
    assert _scoped_key(info, "/etc/passwd") == f"users/{attacker.id}/passwd"
