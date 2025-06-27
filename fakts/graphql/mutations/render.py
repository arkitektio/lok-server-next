import logging

from kante.types import Info

from fakts import inputs, models, scalars

from fakts.logic import render_composition as rc, create_fake_linking_context

logger = logging.getLogger(__name__)


def render_composition(info: Info, input: inputs.RenderInput) -> scalars.Fakt:
    client = models.Client.objects.get(pk=input.client)

    context = create_fake_linking_context(client, "localhost", "8000", secure=False)

    config = rc(client, context)

    return config
