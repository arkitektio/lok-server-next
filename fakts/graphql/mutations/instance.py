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

def update_service_instance(
    info: Info, input: inputs.UpdateServiceInstanceInput
) -> types.ServiceInstance:


    instance = models.ServiceInstance.objects.get(
        id=input.id,
    )

    if input.allowed_groups is not None:
        instance.allowed_groups.set(
            models.Group.objects.filter(id__in=input.allowed_groups)
        )
        
    if input.allowed_users is not None:
        instance.allowed_users.set(
            User.objects.filter(id__in=input.allowed_users)
        )
        
    if input.denied_groups is not None:
        instance.denied_groups.set(
            models.Group.objects.filter(id__in=input.denied_groups)
        )
        
    if input.denied_users is not None:
        instance.denied_users.set(
            User.objects.filter(id__in=input.denied_users)
        )
        
    return instance

