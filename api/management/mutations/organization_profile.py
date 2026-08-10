import logging

import strawberry
from kante.types import Info

from karakter import models
from api.management import types
from api.management.authz import DENIED, assert_owner_or_admin
from graphql import GraphQLError

logger = logging.getLogger(__name__)


@strawberry.input
class CreateOrganizationProfileInput:
    organization: strawberry.ID
    name: str


def create_organization_profile(info: Info, input: CreateOrganizationProfileInput) -> types.ManagementOrganizationProfile:
    try:
        organization = models.Organization.objects.get(pk=input.organization)
    except models.Organization.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_owner_or_admin(info, organization)

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
    try:
        profile = models.OrganizationProfile.objects.get(pk=input.id)
    except models.OrganizationProfile.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_owner_or_admin(info, profile.organization)

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
    try:
        profile = models.OrganizationProfile.objects.get(pk=input.id)
    except models.OrganizationProfile.DoesNotExist:
        raise GraphQLError(DENIED)
    if profile.organization.owner_id != info.context.request.user.id:
        raise GraphQLError(DENIED)
    profile.delete()
    return input.id
