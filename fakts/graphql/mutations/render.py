import logging

from graphql import GraphQLError
from kante.types import Info

from fakts import inputs, models, scalars

from fakts.services.rendering import render_envelope_from_context, create_fake_linking_context
from fakts.types import DENIED

logger = logging.getLogger(__name__)


def render_hub(info: Info, input: inputs.RenderInput) -> scalars.Fakt:
    """Render a client's fakts envelope (self + instances + statuses).

    The envelope no longer carries credentials (auth material travels in OAuth2
    token responses), but instance topology is still tenant-private, so this
    stays scoped to the caller's own organization. It previously fetched by bare
    pk and read `info` not at all.
    """
    try:
        organization = info.context.request.organization
    except Exception:
        raise GraphQLError(DENIED)

    try:
        client = models.Client.objects.get(pk=input.client, organization=organization)
    except models.Client.DoesNotExist:
        # Deliberately the same message as a genuine not-found, so the error
        # cannot be used to probe which client ids exist in other tenants.
        raise GraphQLError(DENIED)

    context = create_fake_linking_context(client, "localhost", "8000", secure=False)

    return render_envelope_from_context(client, context)
