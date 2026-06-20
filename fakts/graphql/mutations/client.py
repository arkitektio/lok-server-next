import hashlib
import json
import logging
import uuid
import strawberry
from kante.types import Info

from fakts import enums, inputs, models, scalars, types
from fakts.base_models import DevelopmentClientConfig, Manifest, Requirement
from fakts.services.clients import create_client

logger = logging.getLogger(__name__)


def create_developmental_client(info: Info, input: inputs.DevelopmentClientInput) -> types.Client:
    token = uuid.uuid4().hex

    config = DevelopmentClientConfig(
        kind=enums.ClientKindVanilla.DEVELOPMENT.value,
        role=enums.ClientRoleVanilla[input.role.name].value if input.role else enums.ClientRoleVanilla.INTERFACE.value,
        token=token,
        tenant=info.context.request.user.username,
        user=info.context.request.user.username,
        organization=info.context.request.organization.slug,
    )

    manifest = Manifest(
        identifier=input.manifest.identifier,
        version=input.manifest.version,
        logo=input.manifest.logo,
        scopes=input.manifest.scopes or [],
        node_id=input.manifest.node_id,
        requirements=[strawberry.asdict(x) for x in input.manifest.requirements],
        public_sources=[strawberry.asdict(x) for x in input.manifest.public_sources] if input.manifest.public_sources else [],
    )

    client = create_client(
        manifest,
        config,
        user=info.context.request.user,
        organization=info.context.request.organization,
        composition=info.context.request.client.composition,
    )

    return client
