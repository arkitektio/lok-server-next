import logging

from kante.types import Info
from django.contrib.auth import get_user_model

from fakts import inputs, models, types


logger = logging.getLogger(__name__)

User = get_user_model()


def update_device(info: Info, input: inputs.UpdateDeviceInput) -> types.Device:
    node = models.Device.objects.get(id=input.id)

    if input.name:
        node.name = input.name

    node.save()
    return node
