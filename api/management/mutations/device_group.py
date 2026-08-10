from kante import Info
import strawberry
from api.management import types
from karakter import models
import kante
from api.management.authz import DENIED, assert_member
from fakts import models as fakts_models
from graphql import GraphQLError


@kante.input
class CreateDeviceGroupInput:
    """Input for creating a single-use magic invite link for an organization"""

    name: str
    organization: strawberry.ID


def create_device_group(info: Info, input: CreateDeviceGroupInput) -> types.ManagementDeviceGroup:
    """ """

    try:
        organization = models.Organization.objects.get(id=input.organization)
    except models.Organization.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, organization)

    dg = fakts_models.DeviceGroup.objects.create(
        name=input.name,
        organization=organization,
    )

    return dg


@kante.input
class DeleteDeviceGroupInput:
    """Input for accepting an organization invite"""

    id: strawberry.ID


def delete_device_group(info: Info, input: DeleteDeviceGroupInput) -> strawberry.ID:
    """
    Accept an invite to join an organization.

    Validates the invite token and adds the user to the organization.
    """
    try:
        dg = fakts_models.DeviceGroup.objects.get(id=input.id)
    except fakts_models.DeviceGroup.DoesNotExist:
        raise GraphQLError(DENIED)

    assert_member(info, dg.organization)

    dg.delete()
    return input.id


@kante.input
class AddDeviceToGroupInput:
    """Input for adding a device to a device group"""

    device: strawberry.ID
    device_group: strawberry.ID


def add_device_to_group(info: Info, input: AddDeviceToGroupInput) -> types.ManagementDevice:
    """ """

    try:
        dg = fakts_models.DeviceGroup.objects.get(id=input.device_group)
    except fakts_models.DeviceGroup.DoesNotExist:
        raise GraphQLError(DENIED)

    try:
        device = fakts_models.Device.objects.get(id=input.device)
    except fakts_models.Device.DoesNotExist:
        raise GraphQLError(DENIED)

    # Both sides must belong to an org the caller is in, and to the *same* org --
    # otherwise membership in one tenant would let you move another tenant's device.
    assert_member(info, dg.organization)
    assert_member(info, device.organization)
    if dg.organization_id != device.organization_id:
        raise GraphQLError(DENIED)

    device.device_groups.add(dg)
    device.save()

    return device


@kante.input
class RemoveDeviceFromGroupInput:
    """Input for removing a device from a device group"""

    device: strawberry.ID
    device_group: strawberry.ID


def remove_device_from_group(info: Info, input: RemoveDeviceFromGroupInput) -> types.ManagementDevice:
    """ """

    try:
        dg = fakts_models.DeviceGroup.objects.get(id=input.device_group)
    except fakts_models.DeviceGroup.DoesNotExist:
        raise GraphQLError(DENIED)

    try:
        device = fakts_models.Device.objects.get(id=input.device)
    except fakts_models.Device.DoesNotExist:
        raise GraphQLError(DENIED)

    # Both sides must belong to an org the caller is in, and to the *same* org --
    # otherwise membership in one tenant would let you move another tenant's device.
    assert_member(info, dg.organization)
    assert_member(info, device.organization)
    if dg.organization_id != device.organization_id:
        raise GraphQLError(DENIED)

    device.device_groups.remove(dg)
    device.save()

    return device
