import strawberry
import strawberry_django
from ekke.types import Info
from fakts import enums, inputs, models, scalars, types


def release(
    info: Info,
    id: strawberry.ID | None = None,
    identifier: scalars.AppIdentifier | None = None,
    version: scalars.Version | None = None,
    client_id: strawberry.ID | None = None,
) -> types.Release:
    
    
    if id is not None:
    
        return models.Release.objects.get(id=id)
    
    elif client_id is not None:
        
        return models.Release.objects.get(
            identifier=identifier, version=version, client_id=client_id
        )
    
    else:
        
        return models.Release.objects.get(
            app__identifier=identifier, version=version
        )
