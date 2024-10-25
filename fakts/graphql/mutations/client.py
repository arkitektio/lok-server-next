import hashlib
import json
import logging
import uuid

import namegenerator
import strawberry
import strawberry_django
from ekke.types import Info

from fakts import enums, inputs, models, scalars, types
from fakts.base_models import DevelopmentClientConfig, Manifest, Requirement
from fakts.builders import create_client
from fakts.models import Composition

logger = logging.getLogger(__name__)




def create_developmental_client(info: Info, input: inputs.DevelopmentClientInput) -> types.Client:


    composition = Composition.objects.get(name=input.composition) if input.composition else Composition.objects.first()
    assert composition, "No composition found"

    token = uuid.uuid4().hex
    
    config = DevelopmentClientConfig(
        kind=enums.ClientKindVanilla.DEVELOPMENT.value,
        composition=composition.name,
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
    )


    return client



