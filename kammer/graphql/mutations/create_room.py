import hashlib
import json
import logging
from typing import Any, Dict, List, Tuple

import strawberry
import strawberry_django
from ekke.types import Info
from komment import enums, inputs, models, scalars, types

logger = logging.getLogger(__name__)
from django.contrib.auth import get_user_model
from komment import inputs


@strawberry.input
class CreateRoomInput:
    description: str | None
    title: str | None


def create_comment(info: Info, input: CreateRoomInput) -> types.Comment:
    creator = info.context.request.user

    serialized_descendants = strawberry.asdict(input)["descendants"]

    dicted_variables, mentions = recurse_parse_decendents(serialized_descendants)

    # TODO: Check if user is allowed to comment on these types of objects

    exp = models.Comment.objects.create(
        identifier=input.identifier,
        object=input.object,
        user=creator,
        text="",
        descendants=serialized_descendants,
        parent_id=input.parent,
    )

    users = [get_user_model().objects.get(id=m["user"]) for m in mentions]
    if input.notify:
        for user in users:
            user.notify(
                f"You have been mentioned in a comment by {creator.username}",
                f"Comment on {input.identifier}",
            )

    print(users)
    exp.mentions.set(users)
    exp.save()

    return exp

    trace = models.User(name=input.user)
    return trace


@strawberry.input
class ReplyToCommentInput:
    descendants: list[inputs.DescendantInput]
    parent: strawberry.ID | None
    notify: bool | None


def reply_to(info: Info, input: ReplyToCommentInput) -> types.Comment:
    raise NotImplementedError("TODO: Implement")


@strawberry.input
class ResolveCommentInput:
    id: strawberry.ID
    notify: bool | None


def resolve_comment(info: Info, input: ResolveCommentInput) -> types.Comment:
    raise NotImplementedError("TODO: Implement")
