from ekke.types import Info
import strawberry_django
import strawberry
from komment import types, models, inputs, enums, scalars
import hashlib
import json
import logging
from karakter.hashers import hash_graph
import namegenerator

logger = logging.getLogger(__name__)


@strawberry.input
class CreateCommentInput:
    descendants: list[inputs.DescendantInput]
    identifier: scalars.Identifier
    object: strawberry.ID
    parent: strawberry.ID | None
    notify: bool


def create_comment(info: Info, input: CreateCommentInput) -> types.Comment:
    trace = models.User(name=input.user)
    return trace
