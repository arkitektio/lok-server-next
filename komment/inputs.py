from komment import enums, scalars
import strawberry
from typing import Optional
from pydantic import BaseModel
from strawberry.experimental import pydantic
from typing import Any
from strawberry import LazyType


class DescendandInputModel(BaseModel):
    kind: enums.DescendantKind
    children: list["DescendandInputModel"] | None = None
    user: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    code: bool | None = None
    text: str | None = None


@pydantic.input(DescendandInputModel)
class DescendantInput:
    kind: enums.DescendantKind
    children: list[LazyType["DescendantInput", __name__]] | None = None
    user: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    code: bool | None = None
    text: str | None = None
