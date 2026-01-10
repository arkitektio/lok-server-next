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
class CreateOrganizationProfileInput:
    organization: strawberry.ID
    name: str


def create_organization_profile(info: Info, input: CreateOrganizationProfileInput) -> types.ManagementOrganizationProfile:
    organization = models.Organization.objects.get(pk=input.organization)
    profile = models.OrganizationProfile(organization=organization, name=input.name)
    profile.save()
    return profile


@strawberry.input
class UpdateOrganizationProfileInput:
    id: strawberry.ID
    name: str | None = None
    banner: strawberry.ID | None = None
    avatar: strawberry.ID | None = None


def update_organization_profile(info: Info, input: UpdateOrganizationProfileInput) -> types.ManagementOrganizationProfile:
    profile = models.OrganizationProfile.objects.get(pk=input.id)
    if input.name:
        profile.name = input.name
    if input.avatar:
        profile.avatar = models.MediaStore.objects.get(pk=input.avatar)
    if input.banner:
        profile.banner = models.MediaStore.objects.get(pk=input.banner)
    profile.save()
    return profile


@strawberry.input
class DeleteOrganizationProfileInput:
    id: strawberry.ID


def delete_organization_profile(info: Info, input: DeleteOrganizationProfileInput) -> strawberry.ID:
    profile = models.OrganizationProfile.objects.get(pk=input.id)
    assert profile.organization.owner == info.context.request.user
    profile.delete()
    return input.id
