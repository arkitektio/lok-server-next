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
class CreateProfileInput:
    user: strawberry.ID
    name: str


def create_profile(info: Info, input: CreateProfileInput) -> types.Profile:
    trace = models.User.objects.get(pk=input.user)
    profile = models.Profile(user=trace, name=input.name)
    profile.save()
    return profile


@strawberry.input
class UpdateProfileInput:
    id: strawberry.ID
    name: str
    avatar: strawberry.ID
    
    
def update_profile(info: Info, input: UpdateProfileInput) -> types.Profile:
    profile = models.Profile.objects.get(pk=input.id)
    profile.name = input.name
    profile.avatar = models.MediaStore.objects.get(pk=input.avatar)
    profile.save()
    return profile




