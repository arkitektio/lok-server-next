from ekke.types import Info
import strawberry_django
import strawberry
from karakter import types, models, inputs, enums, scalars
import hashlib
import json
import logging
from karakter.hashers import hash_graph
import namegenerator

logger = logging.getLogger(__name__)


@strawberry.input
class CreateGroupProfileInput:
    group: strawberry.ID
    name: str
    avatar: strawberry.ID


def create_group_profile(info: Info, input: CreateGroupProfileInput) -> types.GroupProfile:
    trace = models.Group.objects.get(pk=input.group)
    profile = models.GroupProfile(group=trace, name=input.name, avatar=models.MediaStore.objects.get(pk=input.avatar))
    profile.save()
    return profile


@strawberry.input
class UpdateGroupProfileInput:
    id: strawberry.ID
    name: str
    avatar: strawberry.ID
    
    
def update_group_profile(info: Info, input: UpdateGroupProfileInput) -> types.GroupProfile:
    profile = models.GroupProfile.objects.get(pk=input.id)
    profile.name = input.name
    profile.avatar = models.MediaStore.objects.get(pk=input.avatar)
    
    logger.info(f'Updated GroupProfile: {profile.id} with name: {profile.name} and avatar: {profile.avatar}')
    profile.save()
    return profile




