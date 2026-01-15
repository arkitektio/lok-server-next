from kante import Info
import strawberry
from api.management import types
from karakter import models
from django.utils import timezone
from datetime import timedelta
import kante
from fakts import models as fakts_models


@kante.input
class CreateDeviceGroupInput:
    """Input for creating a single-use magic invite link for an organization"""

    name: str
    organization: strawberry.ID


def create_device_group(info: Info, input: CreateDeviceGroupInput) -> types.ManagementDeviceGroup:
    """ """

    user = info.context.request.user
    organization = models.Organization.objects.get(id=input.organization)

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
        raise Exception("Invalid device group ID")

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
        raise Exception("Invalid device group ID")

    try:
        device = fakts_models.ComputeNode.objects.get(id=input.device)
    except fakts_models.ComputeNode.DoesNotExist:
        raise Exception("Invalid device ID")

    device.device_groups.add(dg)
    device.save()

    return device
