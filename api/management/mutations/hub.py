import logging

import strawberry
from kante.types import Info

from api.management import types
from api.management.authz import DENIED, assert_owner_or_admin
from fakts import models as fakts_models
from graphql import GraphQLError

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateHubInput:
    id: strawberry.ID
    name: str | None = None
    description: str | None = None


def update_hub(info: Info, input: UpdateHubInput) -> types.ManagementHub:
    try:
        hub = fakts_models.Hub.objects.get(pk=input.id)
    except fakts_models.Hub.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_owner_or_admin(info, hub.organization)

    # Previously this saved the hub without ever applying the input, so the
    # mutation reported success and changed nothing.
    if input.name is not None:
        hub.name = input.name
    if input.description is not None:
        hub.description = input.description

    hub.save()
    return hub


@strawberry.input
class DeleteHubInput:
    id: strawberry.ID


def delete_hub(info: Info, input: DeleteHubInput) -> strawberry.ID:
    try:
        hub = fakts_models.Hub.objects.get(pk=input.id)
    except fakts_models.Hub.DoesNotExist:
        raise GraphQLError(DENIED)
    if hub.organization.owner_id != info.context.request.user.id:
        raise GraphQLError(DENIED)
    hub.delete()
    return input.id
