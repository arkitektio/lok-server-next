"""GraphQL mutation tests that exercise the schema through the service layer."""

import pytest
from asgiref.sync import sync_to_async
from kante.context import HttpContext, UniversalRequest

from lok_server.schema import schema
from tests import factories


def _context(user, organization, client):
    return HttpContext(
        request=UniversalRequest(
            _extensions={"token": "token"},
            _client=client,  # type: ignore
            _user=user,  # type: ignore
            _organization=organization,  # type: ignore
        ),
        headers={"Authorization": "Bearer token"},
        type="http",
    )


def _setup():
    """Sync DB setup (must not run inside the async event loop)."""
    membership = factories.make_membership()
    # the mutation reads request.client.composition; a fakts Client provides it
    request_client = factories.make_client(membership=membership)
    return membership.user, membership.organization, request_client


CREATE_DEV_CLIENT = """
    mutation Create($input: DevelopmentClientInput!) {
        createDevelopmentalClient(input: $input) {
            id
            kind
            role
        }
    }
"""


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_create_developmental_client_mutation():
    user, organization, request_client = await sync_to_async(_setup)()

    result = await schema.execute(
        CREATE_DEV_CLIENT,
        context_value=_context(user, organization, request_client),
        variable_values={
            "input": {
                "manifest": {
                    "identifier": "com.example.gql",
                    "version": "3.0.0",
                    "scopes": [],
                    "requirements": [],
                },
                "role": "AGENT",
            }
        },
    )

    assert not result.errors, result.errors
    data = result.data["createDevelopmentalClient"]
    assert data["kind"] == "DEVELOPMENT"
    assert data["role"] == "AGENT"

    # verify the created client landed in the DB with the right app/role
    created = await sync_to_async(_fetch_created)()
    assert created is not None


def _fetch_created():
    from fakts import models

    return models.Client.objects.filter(release__app__identifier="com.example.gql", role="agent").first()
