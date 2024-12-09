import strawberry
import strawberry_django
from ekke.types import Info
from fakts import enums, inputs, models, scalars, types


def release(
    info: Info,
    id: strawberry.ID | None,
    identifier: scalars.AppIdentifier | None,
    version: scalars.Version | None,
    client_id: strawberry.ID | None,
) -> types.Release:
    return models.Release.get(id=id)
