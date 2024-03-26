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
from fakts.backends import enums as fb_enums
@strawberry.type(description="A scope that can be assigned to a client. Scopes are used to limit the access of a client to a user's data. They represent app-level permissions.")
class Scope:
    label: str = strawberry.field(description="The label of the scope. This is the human readable name of the scope.")
    description: str = strawberry.field(description="The description of the scope. This is a human readable description of the scope.")
    value: str = strawberry.field(description="The value of the scope. This is the value that is used in the OAuth2 flow.")



@strawberry_django.type(models.Service, description="A Service is a Webservice that a Client might want to access. It is not the configured instance of the service, but the service itself.")
class Service:
    key: str = strawberry.field(description="The key of the service. This is a unique string that identifies the service. It is used to identify the service in the code and in the database.")
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the service")
    identifier: scalars.ServiceIdentifier = strawberry.field(description="The identifier of the service. This should be a globally unique string that identifies the service. We encourage you to use the reverse domain name notation. E.g. `com.example.myservice`")
    logo: str = strawberry.field(description="The logo of the service. This should be a url to a logo that can be used to represent the service.")
    description: str = strawberry.field(description="The description of the service. This should be a human readable description of the service.")

@strawberry_django.type(models.ServiceInstance, description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.")
class ServiceInstance:
    id: strawberry.ID
    service: Service = strawberry.field(description="The service that this instance belongs to.")
    backend: fb_enums.BackendType = strawberry.field(description="The backend that this instance belongs to.")
    composition: "Composition" = strawberry.field(description="The composition that this instance belongs to.")
    name: str = strawberry.field(description="The name of the instance. This is a human readable name of the instance.")
    identifier: str = strawberry.field(description="The identifier of the instance. This is a unique string that identifies the instance. It is used to identify the instance in the code and in the database.")

@strawberry_django.type(models.ServiceInstanceMapping, description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.")
class ServiceInstanceMapping:
    id: strawberry.ID
    instance: ServiceInstance = strawberry.field(description="The service that this instance belongs to.")
    composition: "Composition" = strawberry.field(description="The composition that this instance belongs to.")
    key: str = strawberry.field(description="The key of the instance. This is a unique string that identifies the instance. It is used to identify the instance in the code and in the database.")






@strawberry_django.type(models.Composition)
class Composition:
    id: strawberry.ID 
    name: str  = strawberry.field(description="The name of the composition")
    template: str = strawberry.field(description="The template of the composition. This is a Jinja2 YAML template that will be rendered with the LinkingContext as context. The result of the rendering will be used to send to the client as a configuration. It should never contain sensitive information.")
    mappings: list[ServiceInstanceMapping] = strawberry.field(description="The mappings of the composition. A mapping is a mapping of a service to a service instance. This is used to configure the composition.")
    
   





@strawberry_django.type(models.App, description="An App is the Arkitekt equivalent of a Software Application. It is a collection of `Releases` that can be all part of the same application. E.g the App `Napari` could have the releases `0.1.0` and `0.2.0`.")
class App:
    id: strawberry.ID
    name: str  = strawberry.field(description="The name of the app")
    identifier: scalars.AppIdentifier = strawberry.field(description="The identifier of the app. This should be a globally unique string that identifies the app. We encourage you to use the reverse domain name notation. E.g. `com.example.myapp`")
    logo: str | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")
    releases: list['Release'] = strawberry.field(description="The releases of the app. A release is a version of the app that can be installed by a user.")



@strawberry_django.type(models.Release, description="A Release is a version of an app. Releases might change over time. E.g. a release might be updated to fix a bug, and the release might be updated to add a new feature. This is why they are the home for `scopes` and `requirements`, which might change over the release cycle.")
class Release:
    id: strawberry.ID
    app: App = strawberry.field(description="The app that this release belongs to.")
    version: scalars.Version = strawberry.field(description="The version of the release. This should be a string that identifies the version of the release. We enforce semantic versioning notation. E.g. `0.1.0`. The version is unique per app.")
    name: str = strawberry.field(description="The name of the release. This should be a string that identifies the release beyond the version number. E.g. `canary`.")
    logo: str | None = strawberry.field(description="The logo of the release. This should be a url to a logo that can be used to represent the release.")
    scopes: list[str] = strawberry.field(description="The scopes of the release. Scopes are used to limit the access of a client to a user's data. They represent app-level permissions.")
    requirements: list[str] = strawberry.field(description="The requirements of the release. Requirements are used to limit the access of a client to a user's data. They represent app-level permissions.")
    clients: list['Client'] = strawberry.field(description="The clients of the release")


@strawberry_django.type(Application)
class Oauth2Client:
    id: strawberry.ID
    name: str
    user: types.User
    client_type: str
    algorithm: str
    authorization_grant_type: str
    redirect_uris: str


@strawberry_django.type(models.Client, description="""A client is a way of authenticating users with a release.
 The strategy of authentication is defined by the kind of client. And allows for different authentication flow. 
 E.g a client can be a DESKTOP app, that might be used by multiple users, or a WEBSITE that wants to connect to a user's account, 
 but also a DEVELOPMENT client that is used by a developer to test the app. The client model thinly wraps the oauth2 client model, which is used to authenticate users.""", filters=filters.ClientFilter, pagination=True)
class Client:
    id: strawberry.ID
    release: Release = strawberry.field(description="The release that this client belongs to.")
    tenant: types.User = strawberry.field(description="The user that manages this release.")
    kind: enums.ClientKind = strawberry.field(description="The kind of the client. The kind defines the authentication flow that is used to authenticate users with this client.")
    oauth2_client: Oauth2Client = strawberry.field(description="The real oauth2 client that is used to authenticate users with this client.")
    public: bool = strawberry.field(description="Is this client public? If a client is public ")
    composition: Composition = strawberry.field(description="The composition of the client. ")
    user: types.User | None = strawberry.field(description="If the client is a DEVELOPMENT client, which requires no further authentication, this is the user that is authenticated with the client.")
    token: str = strawberry.field(description="A token that can be used to retrieve the configuration of the client. When providing this token during the configuration flow, the client will received its configuration (the filled in `composition`)")

    @strawberry.field(description="The configuration of the client. This is the configuration that will be sent to the client. It should never contain sensitive information.")
    def kind(self, info) -> enums.ClientKind:
        if self.kind == "website": return enums.ClientKind.WEBSITE
        if self.kind == "desktop": return enums.ClientKind.DESKTOP
        if self.kind == "development": return enums.ClientKind.DEVELOPMENT
        