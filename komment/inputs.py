from komment import enums
import strawberry
from pydantic import BaseModel
from strawberry.experimental import pydantic
from typing import Annotated


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
    children: list[Annotated["DescendantInput", strawberry.lazy(__name__)]] | None = None
    user: str | None = None
    bold: bool | None = None
    italic: bool | None = None
    code: bool | None = None
    text: str | None = None
