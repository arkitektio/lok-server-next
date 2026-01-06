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

logger = logging.getLogger(__name__)


@strawberry.input
class UpdateMembershipInput:
    id: strawberry.ID
    roles: list[strawberry.ID] | None = None


def update_membership(info: Info, input: UpdateMembershipInput) -> types.ManagementMembership:
    profile = models.Membership.objects.get(pk=input.id)
    if input.roles:
        profile.roles.set(models.Role.objects.filter(pk__in=input.roles))
    profile.save()
    return profile


@strawberry.input
class DeleteMembershipInput:
    id: strawberry.ID


def delete_membership(info: Info, input: DeleteMembershipInput) -> strawberry.ID:
    membership = models.Membership.objects.get(pk=input.id)
    assert membership.user == info.context.request.user
    membership.delete()
    return input.id
