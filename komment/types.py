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


class DescendantModel(BaseModel):
    kind: str
    children: list['DescendantUnion'] | None



@pydantic.interface(DescendantModel)
class Descendant:
    kind: enums.DescendantKind
    children: list[LazyType['Descendant',__name__]] | None


class LeafDescendantModel(DescendantModel):
    kind: Literal["LEAF"]
    bold: bool | None
    italic: bool | None
    underline: bool | None
    text: str | None


@pydantic.type(LeafDescendantModel)
class LeafDescendant(Descendant):
    bold: bool | None
    italic: bool | None
    underline: bool | None
    text: str | None



class MentionDescendantModel(DescendantModel):
    kind: Literal["MENTION"]
    user: str | None


@pydantic.type(MentionDescendantModel)
class MentionDescendant(Descendant):
    user: types.User | None



DescendantUnion = Union[LeafDescendantModel, MentionDescendantModel]


@strawberry_django.type(models.Comment)
class Comment:
    id: strawberry.ID
    name: str
    children: list['Comment']
    descendants: list[Descendant]

