import pytest
from lok_server.schema import schema
from kante.context import HttpContext
import pytest_asyncio


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_dataset_upper(db, authenticated_context: HttpContext):

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
                "user": "1",
                "organization": "1",
                "roles": ["labeler"]
            }
        }
    )

    assert sub.data, sub.errors

    assert sub.data["addUserToOrganization"]["roles"][0]["identifier"] == "labeler"
