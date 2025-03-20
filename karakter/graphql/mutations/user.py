from ekke.types import Info
import strawberry_django
import strawberry
from karakter import types, models, inputs, enums, scalars
import hashlib
import json
import logging
from karakter.hashers import hash_graph
import namegenerator

logger = logging.getLogger(__name__)


@strawberry.input
class CreateUserInput:
    name: str


def create_user(info: Info, input: CreateUserInput) -> types.User:
    trace = models.User(name=input.user)
    return trace




