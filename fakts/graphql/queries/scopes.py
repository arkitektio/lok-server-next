import strawberry
import strawberry_django
from kante.types import Info
from fakts import enums, inputs, models, scalars, types


def scopes(info: Info) -> list[types.Scope]:
    return []
