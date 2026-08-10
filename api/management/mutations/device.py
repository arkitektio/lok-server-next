from kante import Info
import strawberry
from api.management import types
from karakter import models
from karakter.hashers import hash_device_id
import kante
from api.management.authz import DENIED, assert_member
from fakts import models as fakts_models
from graphql import GraphQLError


@kante.input
class CreateDeviceInput:
    """Input for creating a single-use magic invite link for an organization"""

    organization: strawberry.ID
    device_id: strawberry.ID
    name: str


def create_device(info: Info, input: CreateDeviceInput) -> types.ManagementDevice:
    """ """
    try:
        organization = models.Organization.objects.get(id=input.organization)
    except models.Organization.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, organization)

    c, _ = fakts_models.Device.objects.update_or_create(organization=organization, node_id=hash_device_id(input.device_id, organization), defaults=dict(name=input.name))

    return c


@kante.input
class UpdateDeviceInput:
    """Input for creating a single-use magic invite link for an organization"""

    id: strawberry.ID
    name: str


def update_device(info: Info, input: UpdateDeviceInput) -> types.ManagementDevice:
    """ """

    try:
        device = fakts_models.Device.objects.get(id=input.id)
    except fakts_models.Device.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, device.organization)

    device.name = input.name
    device.save()

    return device


@kante.input
class DeleteDeviceInput:
    """Input for accepting an organization invite"""

    id: strawberry.ID


def delete_device(info: Info, input: DeleteDeviceInput) -> strawberry.ID:
    """
    Accept an invite to join an organization.

    Validates the invite token and adds the user to the organization.
    """
    try:
        device = fakts_models.Device.objects.get(id=input.id)
    except fakts_models.Device.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, device.organization)

    device.delete()
    return input.id
