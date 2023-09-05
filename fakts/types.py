import strawberry_django
from karakter import models, scalars, enums, filters
import strawberry
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from strawberry.experimental import pydantic
from typing import Any, Dict
from typing import ForwardRef
from strawberry import LazyType
from typing import Literal, Union
from karakter import types
import datetime
from fakts import models, scalars, enums, filters
from oauth2_provider.models import Application


@strawberry_django.type(models.Composition)
class Composition:
    name: str 
    template: str


@strawberry_django.type(models.App)
class App:
    name: str
    identifier: str
    logo: str
    releases: list['Release']



@strawberry_django.type(models.App)
class Release:
    app: App
    version: str
    name: str
    logo: str 
    scopes: list[str]
    requirements: list[str]


@strawberry_django.type(Application)
class Oauth2Client:
    name: str
    user: types.User
    client_type: str
    algorithm: str
    authorization_grant_type: str
    redirect_uris: str


@strawberry_django.type(models.Client)
class Client:
    release: Release
    tenant: types.User
    kind: enums.ClientKind
    oauth2_client: App
    public: bool
    composition: Composition
