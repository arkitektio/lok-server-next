import hashlib
import json
import logging
import uuid

import namegenerator
import strawberry
import strawberry_django
from kante.types import Info

from fakts import enums, inputs, models, scalars, types
from fakts.base_models import DevelopmentClientConfig, Manifest, Requirement
from fakts.builders import create_client
from django.conf import settings

logger = logging.getLogger(__name__)


def create_user_defined_service_instance(
    info: Info, input: inputs.UserDefinedServiceInstanceInput
) -> types.UserDefinedServiceInstance:

    service, _ = models.Service.objects.get_or_create(
        identifier=input.identifier,
        defaults=dict(
            name=input.identifier,
            description=" No description",
        ),
    )

    instance, _ = models.ServiceInstance.objects.get_or_create(
        service=service,
        backend=settings.USER_DEFINED_BACKEND_NAME,
        identifier=service.identifier,
        defaults=dict(template="None"),
    )

    user_defined, _ = models.UserDefinedServiceInstance.objects.update_or_create(
        instance=instance,
        creator=info.context.request.user,
        defaults=dict(
            values=[strawberry.asdict(x) for x in input.values],
        ),
    )

    return user_defined
