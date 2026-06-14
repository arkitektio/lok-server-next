import hashlib
import json
import logging
import uuid

import namegenerator
import strawberry
import strawberry_django
from kante.types import Info
from django.contrib.auth import get_user_model

from fakts import enums, inputs, models, scalars, types

from django.conf import settings

logger = logging.getLogger(__name__)

User = get_user_model()


def update_device(info: Info, input: inputs.UpdateDeviceInput) -> types.Device:
    node = models.Device.objects.get(id=input.id)

    if input.name:
        node.name = input.name

    node.save()
    return node
