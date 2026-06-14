import pytest
from asgiref.sync import sync_to_async

from lok_server.schema import schema
from kante.context import HttpContext
from karakter.models import Organization, User


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_dataset_upper(db, authenticated_context: HttpContext):
    # The roles field is pre-scoped to the request's active organization, so the
    # user must be added to that same org (``testorg``) for the role to be visible.
    org = await sync_to_async(Organization.objects.get)(slug="testorg")
    user = await sync_to_async(User.objects.get)(username="fart")

    ensure_agent = """
        mutation AddUserToOrganization($input: AddUserToOrganizationInput!) {
            addUserToOrganization(input: $input) {
                user {
                    id
                    email
                }
                organization {
                    id
                    name
                }
                roles {
                    id
                    identifier
                }
            }
        }
    """

    sub = await schema.execute(
        ensure_agent,
        context_value=authenticated_context,
        variable_values={
            "input": {
                "user": str(user.id),
                "organization": str(org.id),
                "roles": ["labeler"],
            }
        },
    )

    assert sub.data, sub.errors

    assert sub.data["addUserToOrganization"]["roles"][0]["identifier"] == "labeler"
