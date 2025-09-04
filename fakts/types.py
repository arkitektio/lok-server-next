import strawberry_django
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
from fakts import models, scalars, enums, filters, enums
from karakter.datalayer import get_current_datalayer
from authapp import types as atypes


@strawberry.type(description="Temporary Credentials for a file upload that can be used by a Client (e.g. in a python datalayer)")
class PresignedPostCredentials:
    """Temporary Credentials for a a file upload."""

    key: str
    x_amz_algorithm: str
    x_amz_credential: str
    x_amz_date: str
    x_amz_signature: str
    policy: str
    datalayer: str
    bucket: str
    store: str


@strawberry.type(description="A scope that can be assigned to a client. Scopes are used to limit the access of a client to a user's data. They represent app-level permissions.")
class Scope:
    label: str = strawberry.field(description="The label of the scope. This is the human readable name of the scope.")
    description: str = strawberry.field(description="The description of the scope. This is a human readable description of the scope.")
    value: str = strawberry.field(description="The value of the scope. This is the value that is used in the OAuth2 flow.")


@strawberry_django.type(
    models.Layer,
    description="A Service is a Webservice that a Client might want to access. It is not the configured instance of the service, but the service itself.",
    pagination=True,
    filters=filters.LayerFilter,
)
class Layer:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the layer")
    identifier: scalars.ServiceIdentifier = strawberry.field(description="The identifier of the service. This should be a globally unique string that identifies the service. We encourage you to use the reverse domain name notation. E.g. `com.example.myservice`")
    logo: types.MediaStore | None = strawberry.field(description="The logo of the service. This should be a url to a logo that can be used to represent the service.")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    instances: list["ServiceInstance"] = strawberry_django.field(
        description="The instances of the service. A service instance is a configured instance of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )


@strawberry_django.type(
    models.Service,
    description="A Service is a Webservice that a Client might want to access. It is not the configured instance of the service, but the service itself.",
    pagination=True,
    filters=filters.ServiceFilter,
)
class Service:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the service")
    identifier: scalars.ServiceIdentifier = strawberry.field(description="The identifier of the service. This should be a globally unique string that identifies the service. We encourage you to use the reverse domain name notation. E.g. `com.example.myservice`")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    instances: list["ServiceInstance"] = strawberry_django.field(
        description="The instances of the service. A service instance is a configured instance of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )
    logo: types.MediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")


@strawberry_django.type(
    models.ServiceInstance,
    description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.",
    pagination=True,
    filters=filters.ServiceInstanceFilter,
)
class ServiceInstance:
    id: strawberry.ID
    service: Service = strawberry.field(description="The service that this instance belongs to.")
    name: str = strawberry.field(description="The name of the instance. This is a human readable name of the instance.")
    identifier: str = strawberry.field(description="The identifier of the instance. This is a unique string that identifies the instance. It is used to identify the instance in the code and in the database.")
    allowed_users: list[types.User] = strawberry_django.field(description="The users that are allowed to use this instance.")
    denied_users: list[types.User] = strawberry_django.field(description="The users that are denied to use this instance.")
    allowed_groups: list[types.Group] = strawberry_django.field(description="The groups that are allowed to use this instance.")
    denied_groups: list[types.Group] = strawberry_django.field(description="The groups that are denied to use this instance.")
    mappings: list["ServiceInstanceMapping"] = strawberry_django.field(description="The mappings of the composition. A mapping is a mapping of a service to a service instance. This is used to configure the composition.")
    logo: types.MediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")
    aliases: list["InstanceAlias"] = strawberry_django.field(
        description="The aliases of the instance. An alias is a way to reach the instance. Clients can use these aliases to check if they can reach the instance. An alias can be an absolute alias (e.g. 'example.com') or a relative alias (e.g. 'example.com/path'). If the alias is relative, it will be relative to the layer's domain, port and path."
    )

@strawberry_django.type(
    models.InstanceAlias,
    description="An alias for a service instance. This is used to provide a more user-friendly name for the instance.",
)
class InstanceAlias:
    id: strawberry.ID
    layer: Layer = strawberry.field(description="The layer that this alias belongs to.")
    instance: ServiceInstance = strawberry.field(description="The instance that this alias belongs to.")
    kind: str = strawberry.field(description="The name of the alias. This is a human readable name of the alias.")
    host: Optional[str] = strawberry.field(description="The host of the alias, if its a ABSOLUTE alias (e.g. 'example.com'). If not set, the alias is relative to the layer's domain.")
    port: Optional[int] = strawberry.field(description="The port of the alias, if its a ABSOLUTE alias (e.g. 'example.com:8080'). If not set, the alias is relative to the layer's port.")
    path: Optional[str] = strawberry.field(description="The path of the alias, if its a ABSOLUTE alias (e.g. 'example.com/path'). If not set, the alias is relative to the layer's path.")
    ssl: bool = strawberry.field(description="Is this alias using SSL? If true, the alias will be accessed via https:// instead of http://. This is used to indicate that the alias is secure and should be accessed via SSL")
    challenge: str = strawberry.field(description="The challenge of the alias. This is used to verify that the alias is reachable. If set, the alias will be accessed via the challenge URL (e.g. 'example.com/.well-known/challenge'). If not set, the alias will be accessed via the instance's URL.")

@strawberry_django.type(
    models.ServiceInstanceMapping,
    description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.",
)
class ServiceInstanceMapping:
    id: strawberry.ID
    instance: ServiceInstance = strawberry.field(description="The service that this instance belongs to.")
    client: "Client" = strawberry.field(description="The client that this instance belongs to.")
    key: str = strawberry.field(description="The key of the instance. This is a unique string that identifies the instance. It is used to identify the instance in the code and in the database.")
    optional: bool = strawberry.field(description="Is this mapping optional? If a mapping is optional, you can configure the client without this mapping.")


@strawberry.type
class DefinedValue:
    key: str
    value: str
    as_type: enums.FaktValueType


@strawberry_django.type(
    models.App,
    filters=filters.AppFilter,
    description="An App is the Arkitekt equivalent of a Software Application. It is a collection of `Releases` that can be all part of the same application. E.g the App `Napari` could have the releases `0.1.0` and `0.2.0`.",
    pagination=True,
)
class App:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the app")
    identifier: scalars.AppIdentifier = strawberry.field(description="The identifier of the app. This should be a globally unique string that identifies the app. We encourage you to use the reverse domain name notation. E.g. `com.example.myapp`")

    releases: list["Release"] = strawberry.field(description="The releases of the app. A release is a version of the app that can be installed by a user.")

    logo: types.MediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")


@strawberry_django.type(
    models.Release,
    description="A Release is a version of an app. Releases might change over time. E.g. a release might be updated to fix a bug, and the release might be updated to add a new feature. This is why they are the home for `scopes` and `requirements`, which might change over the release cycle.",
)
class Release:
    id: strawberry.ID
    app: App = strawberry.field(description="The app that this release belongs to.")
    version: scalars.Version = strawberry.field(description="The version of the release. This should be a string that identifies the version of the release. We enforce semantic versioning notation. E.g. `0.1.0`. The version is unique per app.")
    name: str = strawberry.field(description="The name of the release. This should be a string that identifies the release beyond the version number. E.g. `canary`.")
    logo: types.MediaStore | None = strawberry.field(description="The logo of the release. This should be a url to a logo that can be used to represent the release.")
    scopes: list[str] = strawberry.field(description="The scopes of the release. Scopes are used to limit the access of a client to a user's data. They represent app-level permissions.")
    requirements: list[str] = strawberry.field(description="The requirements of the release. Requirements are used to limit the access of a client to a user's data. They represent app-level permissions.")
    clients: list["Client"] = strawberry.field(description="The clients of the release")


@strawberry_django.type(
    models.Client,
    description="""A client is a way of authenticating users with a release.
 The strategy of authentication is defined by the kind of client. And allows for different authentication flow. 
 E.g a client can be a DESKTOP app, that might be used by multiple users, or a WEBSITE that wants to connect to a user's account, 
 but also a DEVELOPMENT client that is used by a developer to test the app. The client model thinly wraps the oauth2 client model, which is used to authenticate users.""",
    filters=filters.ClientFilter,
    pagination=True,
)
class Client:
    id: strawberry.ID
    release: Release = strawberry_django.field(description="The release that this client belongs to.")
    tenant: types.User = strawberry_django.field(description="The user that manages this release.")
    kind: enums.ClientKind = strawberry_django.field(description="The kind of the client. The kind defines the authentication flow that is used to authenticate users with this client.")
    oauth2_client: atypes.Oauth2Client = strawberry_django.field(description="The real oauth2 client that is used to authenticate users with this client.")
    public: bool = strawberry_django.field(description="Is this client public? If a client is public ")
    user: types.User | None = strawberry_django.field(description="If the client is a DEVELOPMENT client, which requires no further authentication, this is the user that is authenticated with the client.")
    logo: types.MediaStore | None = strawberry_django.field(description="The logo of the release. This should be a url to a logo that can be used to represent the release.")
    name: str = strawberry_django.field(description="The name of the client. This is a human readable name of the client.")

    @strawberry_django.field(description="The configuration of the client. This is the configuration that will be sent to the client. It should never contain sensitive information.")
    def kind(self, info) -> enums.ClientKind:
        if self.kind == "website":
            return enums.ClientKind.WEBSITE
        if self.kind == "desktop":
            return enums.ClientKind.DESKTOP
        if self.kind == "development":
            return enums.ClientKind.DEVELOPMENT

    @strawberry.field(description="The configuration of the client. This is the configuration that will be sent to the client. It should never contain sensitive information.")
    def token(self, info) -> str:
        # TODO: Implement only tenant should be able to see the token
        return self.token

    mappings: list["ServiceInstanceMapping"] = strawberry_django.field(description="The mappings of the client. A mapping is a mapping of a service to a service instance. This is used to configure the composition.")


@strawberry_django.type(models.RedeemToken, filters=filters.RedeemTokenFilter, pagination=True)
class RedeemToken:
    id: strawberry.ID
    token: str = strawberry.field(description="The token of the redeem token")
    client: Client | None = strawberry.field(description="The client that this redeem token belongs to.")
    user: types.User = strawberry.field(description="The user that this redeem token belongs to.")

    def get_queryset(cls, info) -> models.RedeemToken:
        return models.RedeemToken.objects.filter(user=info.context.request.user, organization=info.context.request.organization)