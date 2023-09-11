
import strawberry
import strawberry_django
from ekke.types import Info
from fakts import enums, inputs, models, scalars, types


def scopes(info: Info) -> list[types.Scope]:
    return []


