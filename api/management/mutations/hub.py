import logging

import strawberry
from kante.types import Info

from api.management import types
from fakts import models as fakts_models

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateHubInput:
    id: strawberry.ID
    name: str | None = None
    description: str | None = None


def update_hub(info: Info, input: UpdateHubInput) -> types.ManagementHub:
    profile = fakts_models.Hub.objects.get(pk=input.id)

    profile.save()
    return profile


@strawberry.input
class DeleteHubInput:
    id: strawberry.ID


def delete_hub(info: Info, input: DeleteHubInput) -> strawberry.ID:
    hub = fakts_models.Hub.objects.get(pk=input.id)
    assert hub.organization.owner == info.context.request.user, "Only organization owners can delete hubs"
    hub.delete()
    return input.id
