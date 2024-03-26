import hashlib
import json
import logging
import uuid

import namegenerator
import strawberry
import strawberry_django
from ekke.types import Info

from fakts import enums, inputs, models, scalars, types
from fakts.base_models import DevelopmentClientConfig, Manifest
from fakts.builders import create_client
from fakts.models import Composition
from fakts.scan import scan
from fakts.logic import render_composition as rc, create_fake_linking_context

logger = logging.getLogger(__name__)






def render_composition(info: Info, input: inputs.RenderInput) -> scalars.Fakt:


    client = models.Client.objects.get(pk=input.client)
    composition = models.Composition.objects.get(pk=input.composition)

    context = create_fake_linking_context(client, "localhost", "8000", secure=False)

    config = rc(composition, context)


    


    return config



