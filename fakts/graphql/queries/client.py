
import strawberry
import strawberry_django
from ekke.types import Info
from fakts import enums, inputs, models, scalars, types


def client(info: Info, id: strawberry.ID | None,  client_id: strawberry.ID | None) -> types.Client:
    return models.Client.get(id=id)



def my_managed_clients(info: Info, kind: enums.ClientKind) -> types.Client:
    return models.Client.objects.filter(tenant=info.context.request.user, kind=kind)
