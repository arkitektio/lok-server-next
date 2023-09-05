from komment import enums, scalars
import strawberry
from typing import Optional
from pydantic import BaseModel
from strawberry.experimental import pydantic
from typing import Any
from strawberry import LazyType


class DescendandInputModel(BaseModel):
    kind: enums.DescendantKind
    children: list['DescendandInputModel'] | None
    user: str | None
    bold: bool | None
    italic: bool | None
    code: bool | None
    text: str | None


@pydantic.input(DescendandInputModel)
class DescendantInput:
    kind: enums.DescendantKind
    children: list[LazyType["DescendantInput", __name__]] | None
    user: str | None
    bold: bool | None
    italic: bool | None
    code: bool | None
    text: str | None
