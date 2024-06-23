import strawberry_django
from komment import models, scalars, enums, filters
import strawberry
from enum import Enum
from typing import Optional
from typing import Any, Dict
from typing import ForwardRef
from strawberry import LazyType
from typing import Literal, Union
import datetime
from strawberry.experimental import pydantic
from pydantic import BaseModel, Field
from karakter import types
from ekke.types import Info
import json


class DescendantModel(BaseModel):
    kind: str
    children: list["DescendantUnion"] | None


@pydantic.interface(DescendantModel, description="A descendant of a comment. Descendend are used to render rich text in the frontend.")
class Descendant:
    kind: enums.DescendantKind = strawberry.field(description="The Kind of a Descendant")
    children: list[LazyType["Descendant", __name__]] | None = strawberry.field(description="The children of this descendant. Always empty for leafs")

    @strawberry.field(description="Unsafe children are not typed and fall back to json. This is a workaround if queries get too complex.")
    def unsafe_children(self, info: Info) -> list[scalars.UnsafeChild] | None:
        return json.loads(json.dumps(self.children)) if self.children else None


class LeafDescendantModel(DescendantModel):
    kind: Literal["LEAF"]
    bold: bool | None
    italic: bool | None
    underline: bool | None
    text: str | None
    code: str | None


@pydantic.type(LeafDescendantModel, description="A leaf of text. This is the most basic descendant and always ends a tree.")
class LeafDescendant(Descendant):
    bold: bool | None = strawberry.field(description="Should we render this text bold?")
    italic: bool | None = strawberry.field(description="Should we render this text italic?")
    underline: bool | None = strawberry.field(description="Should we render this text underlined?")
    text: str | None = strawberry.field(description="The text of the leaf")
    code: str | None = strawberry.field(description="Should we render this text as code?")


class MentionDescendantModel(DescendantModel):
    kind: Literal["MENTION"]
    user: str | None


@pydantic.type(MentionDescendantModel, description="A mention of a user")
class MentionDescendant(Descendant):
    user: types.User | None = strawberry.field(description="The user that got mentioned")


class ParagraphDescendantModel(DescendantModel):
    kind: Literal["PARAGRAPH"]
    size: str | None


@pydantic.type(ParagraphDescendantModel, description="A Paragraph of text")
class ParagraphDescendant(Descendant):
    size: str | None = strawberry.field(description="The size of the paragraph")


DescendantUnion = Union[
    LeafDescendantModel, MentionDescendantModel, ParagraphDescendantModel
]

DescendantModel.update_forward_refs()
LeafDescendantModel.update_forward_refs()
MentionDescendantModel.update_forward_refs()
ParagraphDescendantModel.update_forward_refs()


class Serializer(BaseModel):
    """ A simple serializer to convert the descendants to a pydantic model. As union types are not supported yet, we need to do this manually."""
    inside: list[DescendantUnion]


@strawberry_django.type(models.Comment)
class Comment:
    id: strawberry.ID
    object: str
    identifier: scalars.Identifier
    children: list["Comment"] = strawberry.field(description="The children of this comment")
    parent: Optional["Comment"]
    created_at: datetime.datetime
    mentions: list[types.User]
    resolved_by: types.User | None
    user: types.User

    @strawberry_django.field
    def descendants(self, info: Info) -> list[Descendant]:
        return Serializer(inside=self.descendants).inside if self.descendants else None

    @strawberry.field
    def resolved(self, info: Info) -> bool:
        return self.resolved_by is not None
