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

logger = logging.getLogger(__name__)


def create_developmental_client(info: Info, input: inputs.DevelopmentClientInput) -> types.Client:
    token = uuid.uuid4().hex

    config = DevelopmentClientConfig(
        kind=enums.ClientKindVanilla.DEVELOPMENT.value,
        token=token,
        tenant=info.context.request.user.username,
        user=info.context.request.user.username,
    )

    manifest = Manifest(
        identifier=input.manifest.identifier,
        version=input.manifest.version,
        logo=input.manifest.logo,
        scopes=input.manifest.scopes or [],
        requirements=[strawberry.asdict(x) for x in input.requirements],
    )

    client = create_client(
        manifest,
        config,
        layers=layers,
        user=info.context.request.user,
    )

    return client
