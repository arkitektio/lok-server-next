from kante.types import Info
import strawberry
from graphql import GraphQLError
from karakter import types, models
from karakter.authz import DENIED, get_user, resolve_own_media_store
import logging

logger = logging.getLogger(__name__)


def _group_the_caller_belongs_to(info: Info, group_id: strawberry.ID) -> models.Group:
    """Fetch a group the caller is a member of, or deny.

    Both resolvers here previously fetched by bare pk with no check at all, so any
    principal could create or overwrite the profile of any group in the
    deployment.
    """
    user = get_user(info)
    try:
        return models.Group.objects.get(pk=group_id, user=user)
    except models.Group.DoesNotExist:
        raise GraphQLError(DENIED)


@strawberry.input
class CreateGroupProfileInput:
    group: strawberry.ID
    name: str
    avatar: strawberry.ID


def create_group_profile(info: Info, input: CreateGroupProfileInput) -> types.GroupProfile:
    trace = _group_the_caller_belongs_to(info, input.group)
    profile = models.GroupProfile(group=trace, name=input.name, avatar=resolve_own_media_store(info, input.avatar, models.MediaStore))
    profile.save()
    return profile


@strawberry.input
class UpdateGroupProfileInput:
    id: strawberry.ID
    name: str
    avatar: strawberry.ID
    
    
def update_group_profile(info: Info, input: UpdateGroupProfileInput) -> types.GroupProfile:
    user = get_user(info)
    try:
        profile = models.GroupProfile.objects.get(pk=input.id, group__user=user)
    except models.GroupProfile.DoesNotExist:
        raise GraphQLError(DENIED)
    profile.name = input.name
    profile.avatar = resolve_own_media_store(info, input.avatar, models.MediaStore)

    logger.info(f'Updated GroupProfile: {profile.id} with name: {profile.name} and avatar: {profile.avatar}')
    profile.save()
    return profile





