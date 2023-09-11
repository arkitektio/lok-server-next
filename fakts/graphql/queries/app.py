
import strawberry
import strawberry_django
from ekke.types import Info
from fakts import enums, inputs, models, scalars, types


def app(info: Info, id: strawberry.ID | None, identifier: scalars.AppIdentifier | None, clientId: strawberry.ID | None) -> types.App:
    return models.App.get(id=id)
