import logging

import strawberry
from kante.types import Info

from karakter import models
from api.management import types
from api.management.authz import DENIED, get_or_denied, get_user
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

    # A post_save signal creates a Profile for every new user, so a plain
    # create() always hit the OneToOne unique constraint: upsert instead.
    profile, _ = models.Profile.objects.update_or_create(user=user, defaults={"name": input.name})
    return profile


@strawberry.input
class UpdateProfileInput:
    id: strawberry.ID
    name: str | None = None
    banner: strawberry.ID | None = None
    avatar: strawberry.ID | None = None


def update_profile(info: Info, input: UpdateProfileInput) -> types.ManagementProfile:
    profile = get_or_denied(models.Profile.objects, pk=input.id)

    if profile.user_id != get_user(info).id:
        raise GraphQLError(DENIED)

    if input.name:
        profile.name = input.name
    if input.avatar:
        profile.avatar = get_or_denied(models.MediaStore.objects, pk=input.avatar)
    if input.banner:
        profile.banner = get_or_denied(models.MediaStore.objects, pk=input.banner)
    profile.save()
    return profile


@strawberry.input
class DeleteProfileInput:
    id: strawberry.ID


def delete_profile(info: Info, input: DeleteProfileInput) -> strawberry.ID:
    profile = get_or_denied(models.Profile.objects, pk=input.id)
    if profile.user_id != get_user(info).id:
        raise GraphQLError(DENIED)
    profile.delete()
    return input.id
