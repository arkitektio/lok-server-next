from ekke.types import Info
import strawberry_django
import strawberry
from fakts import types, models, inputs, enums, scalars
import hashlib
import json
import logging
import namegenerator

logger = logging.getLogger(__name__)


@strawberry.input
class CreateClientInput:
    pass


def create_client(info: Info, input: CreateClientInput) -> types.Client:
    raise NotImplementedError()

