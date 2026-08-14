import pytest
from asgiref.sync import sync_to_async

from lok_server.schema import schema
from kante.context import HttpContext
from karakter.models import Membership, Organization, User

ADD_USER = """
    mutation AddUserToOrganization($input: AddUserToOrganizationInput!) {
        addUserToOrganization(input: $input) {
            user { id email }
            organization { id name }
            roles { id identifier }
        }
    }
"""


async def _add_user(context, user_id, org_id, roles):
    return await schema.execute(
        ADD_USER,
        context_value=context,
        variable_values={"input": {"user": str(user_id), "organization": str(org_id), "roles": roles}},
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_admin_can_add_user_to_organization(db, authenticated_context: HttpContext):
    # The roles field is pre-scoped to the request's active organization, so the
    # user must be added to that same org (``testorg``) for the role to be visible.
    org = await sync_to_async(Organization.objects.get)(slug="testorg")
    caller = await sync_to_async(User.objects.get)(username="fart")
    await sync_to_async(_grant_admin)(caller, org)

    target = await sync_to_async(User.objects.create)(username="newcomer")
    result = await _add_user(authenticated_context, target.id, org.id, ["labeler"])

    assert result.data, result.errors
    assert result.data["addUserToOrganization"]["roles"][0]["identifier"] == "labeler"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_ordinary_member_cannot_add_users(db, authenticated_context: HttpContext):
    """The vulnerability this guard closes.

    ``fart`` is a plain member of ``testorg`` — neither its owner nor an admin.
    Before the fix this mutation had no authorization at all, so any authenticated
    principal could add anyone to any organization with any role, ``admin``
    included.
    """
    org = await sync_to_async(Organization.objects.get)(slug="testorg")
    target = await sync_to_async(User.objects.create)(username="intruder")

    result = await _add_user(authenticated_context, target.id, org.id, ["admin"])

    assert result.errors
    assert not await sync_to_async(
        Membership.objects.filter(user=target, organization=org).exists
    )()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_cannot_add_users_to_a_foreign_organization(db, authenticated_context: HttpContext):
    """Cross-tenant: being an admin somewhere grants nothing elsewhere."""
    org = await sync_to_async(Organization.objects.get)(slug="testorg")
    caller = await sync_to_async(User.objects.get)(username="fart")
    await sync_to_async(_grant_admin)(caller, org)

    other_owner = await sync_to_async(User.objects.create)(username="otherowner")
    other = await sync_to_async(Organization.objects.create)(
        slug="otherorg", name="Other Org", owner=other_owner
    )

    result = await _add_user(authenticated_context, caller.id, other.id, ["admin"])

    assert result.errors
    assert not await sync_to_async(
        Membership.objects.filter(user=caller, organization=other).exists
    )()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_unknown_role_is_rejected_rather_than_half_applied(db, authenticated_context: HttpContext):
    org = await sync_to_async(Organization.objects.get)(slug="testorg")
    caller = await sync_to_async(User.objects.get)(username="fart")
    await sync_to_async(_grant_admin)(caller, org)

    target = await sync_to_async(User.objects.create)(username="rolecheck")
    result = await _add_user(authenticated_context, target.id, org.id, ["labeler", "notarole"])

    assert result.errors
    assert "notarole" in str(result.errors[0])


def _grant_admin(user: User, organization: Organization) -> None:
    from karakter.managers import create_role

    membership, _ = Membership.objects.get_or_create(user=user, organization=organization)
    membership.roles.add(create_role(organization=organization, identifier="admin"))
