from kante import Info
import strawberry
from api.management import types
from karakter import models
from django.utils import timezone
from datetime import timedelta
import kante
from fakts import models as fakts_models


@kante.input
class CreateDeviceInput:
    """Input for creating a single-use magic invite link for an organization"""

    organization: strawberry.ID
    device_id: strawberry.ID
    name: str


def create_device(info: Info, input: CreateDeviceInput) -> types.ManagementDevice:
    """ """
    c, _ = fakts_models.ComputeNode.objects.update_or_create(organization_id=input.organization, node_id=input.device_id, defaults=dict(name=input.name))

    return c


@kante.input
class UpdateDeviceInput:
    """Input for creating a single-use magic invite link for an organization"""

    id: strawberry.ID
    name: str


def update_device(info: Info, input: UpdateDeviceInput) -> types.ManagementDevice:
    """ """

    user = info.context.request.user

    device = fakts_models.ComputeNode.objects.get(id=input.id)
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
        device = fakts_models.ComputeNode.objects.get(id=input.id)
    except fakts_models.ComputeNode.DoesNotExist:
        raise Exception("Invalid device ID")

    device.delete()
    return input.id
