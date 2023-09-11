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


@pydantic.interface(DescendantModel)
class Descendant:
    kind: enums.DescendantKind
    children: list[LazyType["Descendant", __name__]] | None

    @strawberry.field
    def unsafe_children(self, info: Info) -> list[scalars.UnsafeChild] | None:
        return json.loads(json.dumps(self.children)) if self.children else None


class LeafDescendantModel(DescendantModel):
    kind: Literal["LEAF"]
    bold: bool | None
    italic: bool | None
    underline: bool | None
    text: str | None
    code: str | None


@pydantic.type(LeafDescendantModel)
class LeafDescendant(Descendant):
    bold: bool | None
    italic: bool | None
    underline: bool | None
    text: str | None
    code: str | None


class MentionDescendantModel(DescendantModel):
    kind: Literal["MENTION"]
    user: str | None


@pydantic.type(MentionDescendantModel)
class MentionDescendant(Descendant):
    user: types.User | None


class ParagraphDescendantModel(DescendantModel):
    kind: Literal["PARAGRAPH"]
    size: str | None


@pydantic.type(ParagraphDescendantModel)
class ParagraphDescendant(Descendant):
    size: str | None


DescendantUnion = Union[
    LeafDescendantModel, MentionDescendantModel, ParagraphDescendantModel
]

DescendantModel.update_forward_refs()
LeafDescendantModel.update_forward_refs()
MentionDescendantModel.update_forward_refs()
ParagraphDescendantModel.update_forward_refs()


class Serializer(BaseModel):
    inside: list[DescendantUnion]


@strawberry_django.type(models.Comment)
class Comment:
    id: strawberry.ID
    name: str
    object: str
    identifier: scalars.Identifier
    children: list["Comment"]
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
