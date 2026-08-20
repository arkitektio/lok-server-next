"""Session revocation mutations.

Complement the RFC 7009 ``/o/revoke/`` endpoint (which a client uses on its own
tokens) with the operator side: revoke everything issued to one client, or to
every client and hub of an organization. Revoking sets ``OAuth2Token.revoked``,
which kills the refresh chains immediately (the refresh grant is DB-backed);
outstanding JWT access tokens age out within an hour.
"""

import strawberry
from graphql import GraphQLError
from kante import Info

import kante
from api.management import types
from api.management.authz import DENIED, assert_member, assert_owner_or_admin
from authapp.models import OAuth2Token
from fakts import models as fakts_models
from karakter import models


@kante.input
class RevokeClientSessionsInput:
    """Input for revoking every issued token of one client."""

    client: strawberry.ID


def revoke_client_sessions(info: Info, input: RevokeClientSessionsInput) -> types.ManagementClient:
    """Revoke all tokens issued to a client. The client re-authorizes through a
    fresh device-code approval (its refresh chain is dead)."""
    try:
        client = fakts_models.Client.objects.select_related("organization").get(id=input.client)
    except fakts_models.Client.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, client.organization)

    OAuth2Token.objects.filter(client_id=client.client_id).update(revoked=True)

    return client


@kante.input
class RevokeOrganizationSessionsInput:
    """Input for revoking every issued token across an organization."""

    organization: strawberry.ID


def revoke_organization_sessions(info: Info, input: RevokeOrganizationSessionsInput) -> int:
    """Revoke all tokens of every client and hub in an organization (the
    org-level kill switch, e.g. after an incident). Owner/admin only. Returns
    the number of tokens revoked."""
    try:
        organization = models.Organization.objects.get(id=input.organization)
    except models.Organization.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_owner_or_admin(info, organization)

    # Every client in the org — app clients and hub identities alike carry the
    # organization FK on the unified model.
    client_ids = list(
        fakts_models.Client.objects.filter(organization=organization).values_list("client_id", flat=True)
    )

    return OAuth2Token.objects.filter(client_id__in=client_ids, revoked=False).update(revoked=True)
