import logging

import strawberry
from kante.types import Info

from karakter import models
from api.management import types
from api.management.authz import DENIED, get_user
from graphql import GraphQLError

logger = logging.getLogger(__name__)


@strawberry.input
class CreateProfileInput:
    user: strawberry.ID
    name: str


def create_profile(info: Info, input: CreateProfileInput) -> types.ManagementProfile:
    # A profile may only be created for yourself; the `user` input is kept for
    # backwards compatibility but must match the caller.
    user = get_user(info)
    if str(input.user) != str(user.id):
        raise GraphQLError(DENIED)

    profile = models.Profile(user=user, name=input.name)
    profile.save()
    return profile


@strawberry.input
class UpdateProfileInput:
    id: strawberry.ID
    name: str | None = None
    banner: strawberry.ID | None = None
    avatar: strawberry.ID | None = None


def update_profile(info: Info, input: UpdateProfileInput) -> types.ManagementProfile:
    try:
        profile = models.Profile.objects.get(pk=input.id)
    except models.Profile.DoesNotExist:
        raise GraphQLError(DENIED)

    if profile.user_id != get_user(info).id:
        raise GraphQLError(DENIED)

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
    try:
        profile = models.Profile.objects.get(pk=input.id)
    except models.Profile.DoesNotExist:
        raise GraphQLError(DENIED)
    if profile.user_id != get_user(info).id:
        raise GraphQLError(DENIED)
    profile.delete()
    return input.id
