


import hashlib
import json
import logging

import strawberry
from kante.types import Info
from karakter import enums, inputs, models, scalars, types



def mycontext(info: Info) -> types.Context:
    
    
    token = info.context.request.get_extension("token")
    
    
    
    return types.Context(
        user=info.context.request.user,
        organization=info.context.request.organization,
        roles=token.roles,
        scope=token.scopes
    )
    




