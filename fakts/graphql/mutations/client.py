import logging
import strawberry
from kante.types import Info

from fakts import enums, inputs, types
from fakts.base_models import Manifest
from fakts.services.clients import bind_client, create_public_client

logger = logging.getLogger(__name__)


def create_developmental_client(info: Info, input: inputs.DevelopmentClientInput) -> types.Client:
    manifest = Manifest(
        identifier=input.manifest.identifier,
        version=input.manifest.version,
        logo=input.manifest.logo,
        scopes=input.manifest.scopes or [],
        node_id=input.manifest.node_id,
        requirements=[strawberry.asdict(x) for x in input.manifest.requirements],
        public_sources=[strawberry.asdict(x) for x in input.manifest.public_sources] if input.manifest.public_sources else [],
    )

    from karakter.models import Membership

    membership = Membership.objects.get(
        user=info.context.request.user,
        organization=info.context.request.organization,
    )
    client = create_public_client(
        kind=enums.ClientKindVanilla.DEVELOPMENT.value,
        role=enums.ClientRoleVanilla[input.role.name].value if input.role else enums.ClientRoleVanilla.INTERFACE.value,
    )
    client = bind_client(
        client,
        manifest,
        membership,
        hub=info.context.request.client.hub,
    )

    return client
