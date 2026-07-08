import strawberry_django
import strawberry
from typing import Optional
from karakter import types
from fakts import models, scalars, filters, enums
from authapp import types as atypes
from kante.types import Info


def build_prescoped_queryset(info, queryset, field="organization"):
    if info.variable_values.get("filters", {}).get("scope") is None:
        queryset = queryset.filter(**{field: info.context.request.organization})
        return queryset

    else:
        raise Exception("Custom scopes not implemented yet")


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
    ordering=filters.LayerOrdering,
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
    models.Hub,
    ordering=filters.HubOrdering,
    description="A Hub is a specific configuration of a Service. It contains the configuration for a particular version of the service.",
    pagination=True,
    filters=filters.HubFilter,
)
class Hub:
    id: strawberry.ID
    organization: types.Organization = strawberry.field(description="The organization that this hub belongs to.")
    identifier: scalars.ServiceIdentifier = strawberry.field(description="The identifier of the hub. This should be a globally unique string that identifies the hub. We encourage you to use the reverse domain name notation. E.g. `com.example.myhub`")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    name: str = strawberry.field(description="The name of the hub. This should be a human readable name of the hub.")
    


@strawberry_django.type(
    models.Service,
    ordering=filters.ServiceOrdering,
    description="A Service is a Webservice that a Client might want to access. It is not the configured instance of the service, but the service itself.",
    pagination=True,
    filters=filters.ServiceFilter,
)
class Service:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the service")
    identifier: scalars.ServiceIdentifier = strawberry.field(description="The identifier of the service. This should be a globally unique string that identifies the service. We encourage you to use the reverse domain name notation. E.g. `com.example.myservice`")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    releases: list["ServiceRelease"] = strawberry_django.field(
        description="The releases of the service. A service release is a specific version of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )
    logo: types.MediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")


@strawberry_django.type(
    models.ServiceRelease,
    ordering=filters.ServiceReleaseOrdering,
    description="A ServiceRelease is a specific release of a Service. It contains the configuration for a particular version of the service.",
    pagination=True,
    filters=filters.ServiceReleaseFilter,
)
class ServiceRelease:
    id: strawberry.ID
    version: str = strawberry.field(description="The version of the service. This should be a human readable version string.")
    service: Service = strawberry.field(description="The service that this release belongs to.")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    instances: list["ServiceInstance"] = strawberry_django.field(
        description="The instances of the service. A service instance is a configured instance of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )
    


@strawberry_django.type(
    models.ServiceInstance,
    ordering=filters.ServiceInstanceOrdering,
    description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.",
    pagination=True,
    filters=filters.ServiceInstanceFilter,
)
class ServiceInstance:
    id: strawberry.ID
    release: ServiceRelease = strawberry.field(description="The service release that this instance belongs to.")
    instance_id: strawberry.ID = strawberry.field(description="The instance id of the instance. This is a unique string that identifies the instance. It is used to identify the instance in the code and in the database.")  
    name: str = strawberry.field(description="The name of the instance. This is a human readable name of the instance.")
    allowed_users: list[types.User] = strawberry_django.field(description="The users that are allowed to use this instance.")
    denied_users: list[types.User] = strawberry_django.field(description="The users that are denied to use this instance.")
    allowed_groups: list[types.Group] = strawberry_django.field(description="The groups that are allowed to use this instance.")
    denied_groups: list[types.Group] = strawberry_django.field(description="The groups that are denied to use this instance.")
    mappings: list["ServiceInstanceMapping"] = strawberry_django.field(description="The mappings of the hub. A mapping is a mapping of a service to a service instance. This is used to configure the hub.")
    logo: types.MediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")
    aliases: list["InstanceAlias"] = strawberry_django.field(
        description="The aliases of the instance. An alias is a way to reach the instance. Clients can use these aliases to check if they can reach the instance. An alias can be an absolute alias (e.g. 'example.com') or a relative alias (e.g. 'example.com/path'). If the alias is relative, it will be relative to the layer's domain, port and path."
    )


@strawberry_django.type(
    models.InstanceAlias,
    ordering=filters.InstanceAliasOrdering,
    description="An alias for a service instance. This is used to provide a more user-friendly name for the instance.",
)
class InstanceAlias:
    id: strawberry.ID
    layer: Optional[Layer] = strawberry.field(description="The layer that this alias belongs to, if any.")
    instance: ServiceInstance = strawberry.field(description="The instance that this alias belongs to.")
    kind: str = strawberry.field(description="The kind of alias. If relative, the alias is resolved against the layer's domain/port/path; if absolute, it is a full URL.")
    host: Optional[str] = strawberry.field(description="The host of the alias, if its a ABSOLUTE alias (e.g. 'example.com'). If not set, the alias is relative to the layer's domain.")
    port: Optional[int] = strawberry.field(description="The port of the alias, if its a ABSOLUTE alias (e.g. 'example.com:8080'). If not set, the alias is relative to the layer's port.")
    path: Optional[str] = strawberry.field(description="The path of the alias, if its a ABSOLUTE alias (e.g. 'example.com/path'). If not set, the alias is relative to the layer's path.")
    ssl: bool = strawberry.field(description="Is this alias using SSL? If true, the alias will be accessed via https:// instead of http://. This is used to indicate that the alias is secure and should be accessed via SSL")
    challenge: str = strawberry.field(description="The challenge of the alias. This is used to verify that the alias is reachable. If set, the alias will be accessed via the challenge URL (e.g. 'example.com/.well-known/challenge'). If not set, the alias will be accessed via the instance's URL.")
    public: bool = strawberry.field(description="Is this alias publicly reachable? If true, the coordination server can also check the alias's health directly, enabling health checks from the kontrol interface.")


@strawberry_django.type(
    models.ServiceInstanceMapping,
    ordering=filters.ServiceInstanceMappingOrdering,
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
    ordering=filters.AppOrdering,
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
    ordering=filters.ReleaseOrdering,
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


@strawberry.type
class PublicSource:
    kind: str = strawberry.field(description="The kind of the public source. E.g. 'github'")
    url: str = strawberry.field(description="The url of the public source")


@strawberry_django.type(
    models.Client,
    ordering=filters.ClientOrdering,
    description="""A client is a way of authenticating users with a release.
 The strategy of authentication is defined by the kind of client. And allows for different authentication flow. 
 E.g a client can be a DESKTOP app, that might be used by multiple users, or a WEBSITE that wants to connect to a user's account, 
 but also a DEVELOPMENT client that is used by a developer to test the app. The client model thinly wraps the oauth2 client model, which is used to authenticate users.""",
    filters=filters.ClientFilter,
    pagination=True,
)
class Client:
    id: strawberry.ID
    functional: bool = strawberry_django.field(description="Is this client functional? A functional client is a client that is able to authenticate users. If a client is not functional, it will not be able to authenticate users.")
    release: Release = strawberry_django.field(description="The release that this client belongs to.")
    tenant: types.User = strawberry_django.field(description="The user that manages this release.")
    oauth2_client: atypes.Oauth2Client = strawberry_django.field(description="The real oauth2 client that is used to authenticate users with this client.")
    public: bool = strawberry_django.field(description="Is this client public? If a client is public ")
    user: types.User | None = strawberry_django.field(description="If the client is a DEVELOPMENT client, which requires no further authentication, this is the user that is authenticated with the client.")
    logo: types.MediaStore | None = strawberry_django.field(description="The logo of the release. This should be a url to a logo that can be used to represent the release.")
    node: Optional["Device"] = strawberry_django.field(description="The node this runs on")

    @strawberry_django.field(
        description="A human-readable label for the client that folds in the app, version, "
        "operator and device — e.g. `com.example.app:v0.1.1 by Johannes on my-laptop`.",
        select_related=["release__app", "user", "tenant", "node"],
    )
    def name(self, info: Info) -> str:
        release = self.release
        label = f"{release.app.identifier}:v{release.version}" if release else (self.name or "Unknown client")
        person = self.user or self.tenant
        if person:
            full = f"{person.first_name or ''} {person.last_name or ''}".strip()
            label += f" by {full or person.username}"
        if self.node and self.node.name:
            label += f" on {self.node.name}"
        return label
    mappings: list["ServiceInstanceMapping"] = strawberry_django.field(description="The mappings of the client. A mapping is a mapping of a service to a service instance. This is used to configure the hub.")






    @strawberry_django.field(description="The configuration of the client. This is the configuration that will be sent to the client. It should never contain sensitive information.")
    def kind(self, info: Info) -> enums.ClientKind:
        if self.kind == "website":
            return enums.ClientKind.WEBSITE
        if self.kind == "desktop":
            return enums.ClientKind.DESKTOP
        if self.kind == "development":
            return enums.ClientKind.DEVELOPMENT

    @strawberry_django.field(description="The operational role of the client. INTERFACE clients are human interfaces operated by a user in real time. AGENT clients are authorized once and then run unattended, receiving and processing tasks on the user's behalf.")
    def role(self, info: Info) -> enums.ClientRole:
        if self.role == "agent":
            return enums.ClientRole.AGENT
        return enums.ClientRole.INTERFACE

    @strawberry.field(description="The configuration of the client. This is the configuration that will be sent to the client. It should never contain sensitive information.")
    def token(self, info: Info) -> str:
        # TODO: Implement only tenant should be able to see the token
        return self.token

    @strawberry_django.field(description="The issue url of the client. This is the url where users can report issues and get more information about the client.")
    def issue_url(self, info: Info) -> str | None:
        for source in self.public_sources:
            if source.get("kind").lower() == "github":
                return source.get("url") + "/issues/new"

        return None

    @strawberry_django.field(description="The public sources of the client. These are the public sources where users can find more information about the client.")
    def public_sources(self, info: Info) -> list[PublicSource]:
        sources = []
        for source in self.public_sources:
            sources.append(
                PublicSource(
                    kind=source.get("kind"),
                    url=source.get("url"),
                )
            )
        return sources


@strawberry_django.type(
    models.DeviceGroup,
    ordering=filters.DeviceGroupOrdering,
    description="A DeviceGroup is a group of compute nodes that can be used to run clients. DeviceGroups can be used to group compute nodes by location, hardware type, or any other criteria.",
    pagination=True,
    filters=filters.DeviceGroupFilter,
)
class DeviceGroup:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the device group.")
    description: str | None = strawberry.field(description="The description of the device group.")
    devices: list["Device"] = strawberry_django.field(description="The devices that belong to this device group.")

    def get_queryset(cls, info) -> models.DeviceGroup:
        return models.DeviceGroup.objects.filter(organization=info.context.request.organization)


@strawberry_django.type(models.Device, filters=filters.DeviceFilter, pagination=True, ordering=filters.DeviceOrdering)
class Device:
    id: strawberry.ID
    name: str | None
    node_id: strawberry.ID
    clients: list[Client]
    device_groups: list[DeviceGroup] = strawberry_django.field(description="The device groups that belong to this device.")

    def get_queryset(cls, info) -> models.Device:
        return models.Device.objects.filter(organization=info.context.request.organization)


@strawberry_django.type(models.RedeemToken, filters=filters.RedeemTokenFilter, pagination=True, ordering=filters.RedeemTokenOrdering)
class RedeemToken:
    id: strawberry.ID
    token: str = strawberry.field(description="The token of the redeem token")
    client: Client | None = strawberry.field(description="The client that this redeem token belongs to.")
    user: types.User = strawberry.field(description="The user that this redeem token belongs to.")

    def get_queryset(cls, info) -> models.RedeemToken:
        return models.RedeemToken.objects.filter(user=info.context.request.user, hub__organization=info.context.request.organization)
