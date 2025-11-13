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
from fakts.base_models import DevelopmentClientConfig, Manifest, Requirement
from fakts.builders import create_client
from django.conf import settings

logger = logging.getLogger(__name__)

User = get_user_model()


def update_compute_node(info: Info, input: inputs.UpdateComputeNodeInput) -> types.ComputeNode:
    node = models.ComputeNode.objects.get(id=input.id)

    if input.name:
        node.name = input.name

    node.save()
    return node
