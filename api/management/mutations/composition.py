import hashlib
import json
import logging

import namegenerator
import strawberry
import strawberry_django
from kante.types import Info

from karakter import enums, inputs, models, scalars
from karakter.hashers import hash_graph
from api.management import types
from fakts import models as fakts_models

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateCompositionInput:
    id: strawberry.ID
    name: str | None = None
    description: str | None = None


def update_composition(info: Info, input: UpdateCompositionInput) -> types.ManagementComposition:
    profile = fakts_models.Composition.objects.get(pk=input.id)

    profile.save()
    return profile


@strawberry.input
class DeleteCompositionInput:
    id: strawberry.ID


def delete_composition(info: Info, input: DeleteCompositionInput) -> strawberry.ID:
    composition = fakts_models.Composition.objects.get(pk=input.id)
    assert composition.organization.owner == info.context.request.user, "Only organization owners can delete compositions"
    composition.delete()
    return input.id
