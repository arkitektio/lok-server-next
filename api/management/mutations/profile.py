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
class CreateProfileInput:
    user: strawberry.ID
    name: str


def create_profile(info: Info, input: CreateProfileInput) -> types.ManagementProfile:
    trace = models.User.objects.get(pk=input.user)
    profile = models.Profile(user=trace, name=input.name)
    profile.save()
    return profile


@strawberry.input
class UpdateProfileInput:
    id: strawberry.ID
    name: str | None = None
    banner: strawberry.ID | None = None
    avatar: strawberry.ID | None = None


def update_profile(info: Info, input: UpdateProfileInput) -> types.ManagementProfile:
    profile = models.Profile.objects.get(pk=input.id)
    if input.name:
        profile.name = input.name
    if input.avatar:
        profile.avatar = models.MediaStore.objects.get(pk=input.avatar)
    if input.banner:
        profile.banner = models.MediaStore.objects.get(pk=input.banner)
    profile.save()
    return profile


@strawberry.input
class DeleteProfileInput:
    id: strawberry.ID


def delete_profile(info: Info, input: DeleteProfileInput) -> strawberry.ID:
    profile = models.Profile.objects.get(pk=input.id)
    assert profile.user == info.context.request.user
    profile.delete()
    return input.id
