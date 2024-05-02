
import strawberry
import strawberry_django
from ekke.types import Info
from fakts import enums, inputs, models, scalars, types


def app(info: Info, id: strawberry.ID | None = None, identifier: scalars.AppIdentifier | None = None, client_id: strawberry.ID | None = None)  -> types.App:
    if id:
        return models.App.objects.get(id=id)
    
    if identifier:
        return models.App.objects.get(identifier=identifier)
    
    if client_id:
        return models.Client.objects.get(client_id=client_id).release.app

    raise ValueError("Either id or identifier or clientId must be provided")
