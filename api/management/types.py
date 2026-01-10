import datetime
from enum import Enum
from typing import Any, Dict, ForwardRef, List, Optional, cast
from karakter.datalayer import get_current_datalayer
import strawberry
import strawberry_django
from kante.types import Info
from karakter import enums, models, scalars
from strawberry import LazyType
from allauth.socialaccount import models as smodels
import kante
from fakts import models as fakts_models
from fakts import filters as fakts_filters
from fakts import scalars as fakts_scalars
from fakts import base_models
from api.management import filters, enums, scalars
from karakter import models as karakter_models
from karakter import filters as karakter_filters
from strawberry.experimental import pydantic


def build_prescoper(field="organization"):
    def prescoper(queryset, info):
        return queryset

    return prescoper


@strawberry_django.type(
    models.Group,
    filters=karakter_filters.GroupFilter,
    pagination=True,
    description="""
A Group is the base unit of Role Based Access Control. A Group can have many users and many permissions. A user can have many groups. A user with a group that has a permission can perform the action that the permission allows.
Groups are propagated to the respecting subservices. Permissions are not. Each subservice has to define its own permissions and mappings to groups.
""",
)
class ManagementGroup:
    id: strawberry.ID
    name: str
    profile: Optional["ManagementGroupProfile"]

    @strawberry_django.field(description="The users that are in the group")
    def users(self, info: Info) -> List["ManagementUser"]:
        return models.User.objects.filter(groups=self)


@strawberry_django.type(models.MediaStore)
class ManagementMediaStore:
    id: strawberry.ID
    path: str
    bucket: str
    key: str

    @strawberry_django.field()
    def presigned_url(self, info: Info, host: str | None = None) -> str:
        datalayer = get_current_datalayer()
        return cast(models.MediaStore, self).get_presigned_url(info, datalayer=datalayer, host=host)


@strawberry_django.type(
    models.User,
    filters=karakter_filters.UserFilter,
    pagination=True,
    description="""
A User is a person that can log in to the system. They are uniquely identified by their username.
And can have an email address associated with them (but don't have to).

A user can be assigned to groups and has a profile that can be used to display information about them.
Detail information about a user can be found in the profile.

All users can have social accounts associated with them. These are used to authenticate the user with external services,
such as ORCID or GitHub.

""",
)
class ManagementUser:
    id: strawberry.ID
    username: str
    first_name: str | None
    last_name: str | None
    email: str | None
    groups: list[ManagementGroup]
    memberships: list["ManagementMembership"] = strawberry_django.field(description="The memberships of the user in organizations")
    avatar: str | None
    profile: "ManagementProfile"
    com_channels: list["ManagementComChannel"] = strawberry_django.field(description="The communication channels that the user has")

    @strawberry_django.field(description="The full name of the user")
    def social_accounts(self, info: Info) -> List["ManagementSocialAccount"]:
        return smodels.SocialAccount.objects.filter(user_id=self.id)


@strawberry_django.type(
    models.Profile,
    filters=karakter_filters.ProfileFilter,
    pagination=True,
    description="""
A Profile of a User. A Profile can be used to display personalied information about a user.

""",
)
class ManagementProfile:
    id: strawberry.ID
    bio: str | None = strawberry.field(description="A short bio of the user")
    name: str | None = strawberry.field(description="The name of the user")
    avatar: ManagementMediaStore | None = strawberry.field(description="The avatar of the user")
    banner: ManagementMediaStore | None = strawberry.field(description="The banner of the user")


@strawberry_django.type(
    models.OrganizationProfile,
    filters=karakter_filters.OrganizationFilter,
    pagination=True,
    description="""
A Profile of a User. A Profile can be used to display personalied information about a user.

""",
)
class ManagementOrganizationProfile:
    id: strawberry.ID
    organization: "ManagementOrganization"
    bio: str | None = strawberry.field(description="A short bio of the user")
    name: str | None = strawberry.field(description="The name of the user")
    avatar: ManagementMediaStore | None = strawberry.field(description="The avatar of the organization")
    banner: ManagementMediaStore | None = strawberry.field(description="The banner of the organization")


@strawberry_django.type(
    models.GroupProfile,
    filters=karakter_filters.GroupProfileFilter,
    pagination=True,
    description="""
A Profile of a User. A Profile can be used to display personalied information about a user.

""",
)
class ManagementGroupProfile:
    id: strawberry.ID
    bio: str | None = strawberry.field(description="A short bio of the group")
    name: str | None = strawberry.field(description="The name of the group")
    avatar: ManagementMediaStore | None = strawberry.field(description="The avatar of the group")


@strawberry_django.interface(
    smodels.SocialAccount,
    description="""
A Social Account is an account that is associated with a user. It can be used to authenticate the user with external services. It
can be used to store extra data about the user that is specific to the provider. We provide typed access to the extra data for
some providers. For others we provide a generic json field that can be used to store arbitrary data. Generic accounts are
always available, but typed accounts are only available for some providers.
""",
)
class ManagementSocialAccount:
    id: strawberry.ID
    provider: str = strawberry.field(description="The provider of the account. This can be used to determine the type of the account.")
    uid: str = strawberry.field(description="The unique identifier of the account. This is unique for the provider.")
    extra_data: scalars.ExtraData = strawberry.field(description="Extra data that is specific to the provider. This is a json field and can be used to store arbitrary data.")

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return queryset.filter(user=info.context.request.user)


@strawberry.type(description="""The ORCID Identifier of a user. This is a unique identifier that is used to identify a user on the ORCID service. It is composed of a uri, a path and a host.""")
class ManagementOrcidIdentifier:
    uri: str = strawberry.field(description="The uri of the identifier")
    path: str = strawberry.field(description="The path of the identifier")
    host: str = strawberry.field(description="The host of the identifier")


@strawberry.type(description="""The ORCID Preferences of a user. This is a set of preferences that are specific to the ORCID service. Currently only the locale is supported.""")
class ManagementOrcidPreferences:
    locale: str = strawberry.field(description="The locale of the user. This is used to determine the language of the ORCID service.")


@strawberry.type(description="""Assoiated OridReseracher Result""")
class ManagementOrcidResearcherURLS:
    path: str
    urls: list[str]


@strawberry.type()
class ManagementOrcidAddresses:
    path: str
    addresses: list[str]


@strawberry.type()
class ManagementOrcidPerson:
    researcher_urls: list[str]
    addresses: list[str]


@strawberry.type()
class ManagementOrcidActivities:
    educations: list[str]


@strawberry_django.type(
    smodels.SocialAccount,
    filters=karakter_filters.SocialAccountFilter,
    pagination=True,
    description="""
An ORCID Account is a Social Account that maps to an ORCID Account. It provides information about the
user that is specific to the ORCID service. This includes the ORCID Identifier, the ORCID Preferences and
the ORCID Person. The ORCID Person contains information about the user that is specific to the ORCID service.
This includes the ORCID Activities, the ORCID Researcher URLs and the ORCID Addresses.

""",
)
class ManagementOrcidAccount(ManagementSocialAccount):
    @strawberry_django.field(description="The ORCID Identifier of the user. The UID of the account is the same as the path of the identifier.")
    def identifier(self) -> ManagementOrcidIdentifier:
        return ManagementOrcidIdentifier(**self.extra_data["orcid-identifier"])

    @strawberry_django.field(description="Information about the person that is specific to the ORCID service.")
    def person(self) -> Optional[ManagementOrcidPerson]:
        person = self.extra_data.get("person", None)
        if not person:
            return None

        researcher_urls = self.extra_data.get("researcher-urls", {}).get("researcher-urls", [])
        addresses = self.extra_data.get("addresses", {}).get("addresses", [])

        return ManagementOrcidPerson(researcher_urls=researcher_urls, addresses=addresses)

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider == "orcid"


@strawberry_django.type(
    smodels.SocialAccount,
    filters=karakter_filters.SocialAccountFilter,
    pagination=True,
    description="""
The Github Account is a Social Account that maps to a Github Account. It provides information about the
user that is specific to the Github service. This includes the Github Identifier.

""",
)
class ManagementGithubAccount(ManagementSocialAccount):
    @strawberry_django.field()
    def identifier(self) -> ManagementOrcidIdentifier:
        raise NotImplementedError()

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider == "github"


@strawberry_django.type(
    smodels.SocialAccount,
    filters=karakter_filters.SocialAccountFilter,
    pagination=True,
    description="""
The Generic Account is a Social Account that maps to a generic account. It provides information about the
user that is specific to the provider. This includes untyped extra data.

""",
)
class ManagementGenericAccount(ManagementSocialAccount):
    extra_data: scalars.ExtraData

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider != "orcid"


@strawberry_django.type(
    smodels.SocialAccount,
    pagination=True,
    description="""
The Generic Account is a Social Account that maps to a generic account. It provides information about the
user that is specific to the provider. This includes untyped extra data.

""",
)
class ManagementGoogleAccount(ManagementSocialAccount):
    extra_data: scalars.ExtraData

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider != "orcid"


@strawberry_django.type(
    smodels.SocialAccount,
    pagination=True,
    description="""
The Generic Account is a Social Account that maps to a generic account. It provides information about the
user that is specific to the provider. This includes untyped extra data.

""",
)
class ManagementGenericAccount(ManagementSocialAccount):
    extra_data: scalars.ExtraData

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider != "orcid"


@strawberry.type(description="""A Communication""")
class ManagementCommunication:
    channel: strawberry.ID


@strawberry_django.type(
    models.SystemMessage,
    filters=karakter_filters.ProfileFilter,
    pagination=True,
    description="""
A System Message is a message that is sent to a user. 
It can be used to notify the user of important events or to request their attention.
System messages can use Rekuest Hooks as actions to allow the user to interact with the message.


""",
)
class ManagementSystemMessage:
    id: strawberry.ID
    title: str
    message: str
    action: str
    user: ManagementUser


@strawberry_django.type(models.Role, filters=filters.ManagementRoleFilter, order=filters.ManagementRoleOrder, pagination=True, description="""A Role is a set of permissions that can be assigned to a user. It is used to define what a user can do in the system.""")
class ManagementRole:
    id: strawberry.ID
    identifier: str
    organization: "ManagementOrganization"
    creating_instance: Optional["ManagementServiceInstance"]
    memberships: List["ManagementMembership"] = strawberry.django.field(description="The memberships that have this role")
    used_by: List["ManagementServiceInstance"] = strawberry.django.field(description="The service instances that use this role")

    @kante.django_field()
    def description(self, info: Info) -> "str":
        return self.description or self.identifier

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        print(info.context.request.user)
        return queryset.filter(organization__memberships__user=info.context.request.user).distinct()


@strawberry_django.type(models.Scope, filters=filters.ManagementScopeFilter, order=filters.ManagementScopeOrder, pagination=True, description="""A Role is a set of permissions that can be assigned to a user. It is used to define what a user can do in the system.""")
class ManagementScope:
    id: strawberry.ID
    identifier: str
    organization: "ManagementOrganization"
    creating_instance: Optional["ManagementServiceInstance"]
    memberships: List["ManagementMembership"] = strawberry.django.field(description="The memberships that have this role")
    used_by: List["ManagementServiceInstance"] = strawberry.django.field(description="The service instances that use this scope")

    @kante.django_field()
    def description(self, info: Info) -> "str":
        return self.description or self.identifier

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        print(info.context.request.user)
        return queryset.filter(organization__memberships__user=info.context.request.user).distinct()


@strawberry_django.type(
    models.Membership,
    filters=filters.ManagementMembershipFilter,
    order=filters.ManagementMembershipOrder,
    pagination=True,
    description="""
A Membership is a relation between a User and an Organization. It can have multiple Roles assigned to it.
""",
)
class ManagementMembership:
    id: strawberry.ID
    user: ManagementUser
    organization: "ManagementOrganization"
    roles: List["ManagementRole"] = strawberry.field(description="The roles that the user has in the organization")
    created_through: Optional["ManagementInvite"] = strawberry.field(description="The invite that created this membership")


@strawberry_django.type(models.Organization, filters=karakter_filters.OrganizationFilter, pagination=True, description="""An Organization is a group of users that can work together on a project.""")
class ManagementOrganization:
    id: strawberry.ID
    slug: str
    description: str | None = strawberry.field(description="A short description of the organization")
    users: List[ManagementUser] = strawberry.field(description="The users that are part of the organization")
    active_users: List[ManagementUser] = strawberry.field(description="The users that are currently active in the organization")
    profile: Optional["ManagementOrganizationProfile"] = strawberry.field(description="The profile of the organization")
    memberships: List["ManagementMembership"] = strawberry_django.field(description="the memberships of people")
    invites: List["ManagementInvite"] = strawberry_django.field(description="the invites for this organization")
    clients: List["ManagementClient"] = strawberry_django.field(description="The clients that belong to this organization")
    service_instances: List["ManagementServiceInstance"] = strawberry_django.field(description="The service instances that belong to this organization")

    @strawberry_django.field(description="The roles that are available in the organization")
    def roles(self) -> List["ManagementRole"]:
        return self.roles.all()

    @strawberry_django.field(description="The name of this organization")
    def name(self) -> str:
        return self.name or self.slug

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        print(info.context.request.user)
        return queryset.filter(memberships__user=info.context.request.user).distinct()


@strawberry_django.type(models.ComChannel, filters=karakter_filters.OrganizationFilter, pagination=True, description="""An Organization is a group of users that can work together on a project.""")
class ManagementComChannel:
    id: strawberry.ID
    user: ManagementUser


@strawberry_django.type(models.Invite, filters=karakter_filters.OrganizationFilter, pagination=True, description="""A single-use magic invite link that allows one person to join an organization.""")
class ManagementInvite:
    id: strawberry.ID
    token: str
    email: str | None
    created_by: ManagementUser
    created_for: ManagementOrganization
    created_at: datetime.datetime
    expires_at: datetime.datetime | None
    status: str
    accepted_by: ManagementUser | None
    declined_by: ManagementUser | None
    responded_at: datetime.datetime | None
    roles: list["ManagementRole"]
    created_memberships: list["ManagementMembership"]

    @strawberry_django.field(description="Check if the invite is still valid and pending")
    def valid(self) -> bool:
        """Check if the invite is still valid"""
        return self.is_valid()

    @strawberry_django.field(description="Get the full URL for accepting this invite")
    def invite_url(self, info: Info) -> str:
        """Generate the full URL for accepting this invite"""
        from django.urls import reverse

        request = info.context.request
        path = reverse("accept_invite", kwargs={"token": str(self.token)})
        return path


@pydantic.type(base_models.Requirement)
class ManagementStagingRequirement:
    service: str
    key: str
    description: str | None = None
    optional: bool = False


@pydantic.type(base_models.PublicSource)
class ManagementStagingPublicSource:
    kind: str
    url: str


@pydantic.type(base_models.Manifest)
class ManagementStagingManifest:
    version: str
    identifier: str
    description: str | None = None
    url: str | None = None
    logo: str | None = None
    scopes: list[str]
    node_id: strawberry.ID
    repo_url: str | None = None
    public_sources: list[ManagementStagingPublicSource] | None = strawberry.field(description="Public sources for this staging service")
    requirements: list[ManagementStagingRequirement]


@pydantic.type(base_models.Role)
class StagingRole:
    key: str
    description: str | None = None


@pydantic.type(base_models.Scope)
class StagingScope:
    key: str
    description: str | None = None


@pydantic.type(base_models.StagingAlias)
class StagingAlias:
    id: strawberry.ID
    kind: str
    name: Optional[str]
    host: Optional[str]
    port: Optional[int]
    ssl: bool = False
    path: Optional[str] = None
    challenge: Optional[str] = None


@pydantic.type(base_models.ServiceManifest)
class ManagementStagingServiceManifest:
    version: str
    identifier: str
    description: str | None = None
    logo: str | None = None
    scopes: list[StagingScope] | None = None
    node_id: strawberry.ID
    roles: list[StagingRole] | None = None
    instance_id: str
    public_sources: list[ManagementStagingPublicSource]


@pydantic.type(base_models.InstanceRequest)
class ManagementStagingInstanceRequest:
    manifest: ManagementStagingServiceManifest
    aliases: list[StagingAlias] | None = None
    identifier: str
    description: Optional[str] = None


@pydantic.type(base_models.ClientRequest)
class ManagementStagingClientRequest:
    manifest: ManagementStagingManifest
    identifier: str
    description: Optional[str] = None


@pydantic.type(base_models.CompositionManifest)
class ManagementCompositionManifest:
    identifier: str
    instances: list[ManagementStagingInstanceRequest]
    clients: list[ManagementStagingClientRequest]


@strawberry_django.type(
    fakts_models.Service,
    description="A Service is a Webservice that a Client might want to access. It is not the configured instance of the service, but the service itself.",
    pagination=True,
    filters=fakts_filters.ServiceFilter,
)
class ManagementService:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the service")
    identifier: fakts_scalars.ServiceIdentifier = strawberry.field(description="The identifier of the service. This should be a globally unique string that identifies the service. We encourage you to use the reverse domain name notation. E.g. `com.example.myservice`")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    releases: list["ManagementServiceRelease"] = strawberry_django.field(
        description="The releases of the service. A service release is a configured instance of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )
    logo: ManagementMediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")


@strawberry.type(description="Result of validating a device code against an organization")
class PotentialMapping:
    service_instance: Optional["ManagementServiceInstance"]
    key: str
    reason: str | None


@strawberry.type
class ValidationResult:
    valid: bool
    reason: str | None
    mappings: list[PotentialMapping]


@strawberry_django.type(
    fakts_models.ServiceRelease,
    description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.",
    pagination=True,
    filters=fakts_filters.ServiceInstanceFilter,
)
class ManagementServiceRelease:
    id: strawberry.ID
    service: ManagementService = strawberry.field(description="The service that this instance belongs to.")
    version: str = strawberry.field(description="The version of the service release.")
    instances: list["ManagementServiceInstance"] = strawberry_django.field(
        description="The instances of the service release. A service instance is a configured instance of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )


@strawberry_django.type(
    fakts_models.ServiceInstance,
    description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.",
    pagination=True,
    filters=filters.ManagementServiceInstanceFilter,
    order=filters.ManagementServiceInstanceOrder,
)
class ManagementServiceInstance:
    id: strawberry.ID
    release: ManagementServiceRelease = strawberry.field(description="The service that this instance belongs to.")
    organization: "ManagementOrganization" = strawberry.field(description="The organization that owns this instance.")
    device: Optional["ManagementDevice"] = strawberry.field(description="The device that this instance is associated with, if any.")
    instance_id: str = strawberry.field(description="The identifier of the instance. This is a unique string that identifies the instance. It is used to identify the instance in the code and in the database.")
    allowed_users: list[ManagementUser] = strawberry_django.field(description="The users that are allowed to use this instance.")
    denied_users: list[ManagementUser] = strawberry_django.field(description="The users that are denied to use this instance.")
    allowed_groups: list[ManagementGroup] = strawberry_django.field(description="The groups that are allowed to use this instance.")
    denied_groups: list[ManagementGroup] = strawberry_django.field(description="The groups that are denied to use this instance.")
    mappings: list["ManagementServiceInstanceMapping"] = strawberry_django.field(description="The mappings of the composition. A mapping is a mapping of a service to a service instance. This is used to configure the composition.")
    logo: ManagementMediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")
    aliases: list["ManagementInstanceAlias"] = strawberry_django.field(
        description="The aliases of the instance. An alias is a way to reach the instance. Clients can use these aliases to check if they can reach the instance. An alias can be an absolute alias (e.g. 'example.com') or a relative alias (e.g. 'example.com/path'). If the alias is relative, it will be relative to the layer's domain, port and path."
    )
    roles: list["ManagementRole"] = strawberry_django.field(description="The roles that are associated with this instance. These roles will be assigned to users that are allowed to use this instance.")
    scopes: list["ManagementScope"] = strawberry_django.field(description="The scopes that are associated with this instance. These scopes will be assigned to users that are allowed to use this instance.")

    @strawberry_django.field(description="The steward of the instance. The steward is the user who is responsible for this instance.")
    def identifier(self) -> str:
        return f"{self.instance_id} @ {self.device.name if self.device else 'no-device'} @ {self.organization.slug}"


@strawberry_django.type(
    fakts_models.Composition,
    description="A Service is a Webservice that a Client might want to access. It is not the configured instance of the service, but the service itself.",
    pagination=True,
    filters=filters.ManagementCompositionFilter,
    order=filters.ManagementCompositionOrder,
)
class ManagementComposition:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the layer")
    logo: ManagementMediaStore | None = strawberry.field(description="The logo of the service. This should be a url to a logo that can be used to represent the service.")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    instances: list["ManagementServiceInstance"] = strawberry_django.field(
        description="The instances of the service. A service instance is a configured instance of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )
    organization: "ManagementOrganization" = strawberry.field(description="The organization that owns this composition.")
    clients: list["ManagementClient"] = strawberry_django.field(description="The clients that are part of this composition. A client is an application that uses the services in the composition.")

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return queryset.filter(organization__memberships__user=info.context.request.user).distinct()


@strawberry_django.type(
    fakts_models.InstanceAlias,
    description="An alias for a service instance. This is used to provide a more user-friendly name for the instance.",
    filters=filters.ManagementInstanceAliasFilter,
    order=filters.ManagementInstanceAliasOrder,
    pagination=True,
)
class ManagementInstanceAlias:
    id: strawberry.ID
    organization: "ManagementOrganization" = strawberry.field(description="The organization that owns this alias.")
    layer: Optional["ManagementLayer"] = strawberry.field(description="The layer that this alias belongs to.")
    instance: ManagementServiceInstance = strawberry.field(description="The instance that this alias belongs to.")
    kind: str = strawberry.field(description="The name of the alias. This is a human readable name of the alias.")
    host: Optional[str] = strawberry.field(description="The host of the alias, if its a ABSOLUTE alias (e.g. 'example.com'). If not set, the alias is relative to the layer's domain.")
    port: Optional[int] = strawberry.field(description="The port of the alias, if its a ABSOLUTE alias (e.g. 'example.com:8080'). If not set, the alias is relative to the layer's port.")
    path: Optional[str] = strawberry.field(description="The path of the alias, if its a ABSOLUTE alias (e.g. 'example.com/path'). If not set, the alias is relative to the layer's path.")
    ssl: bool = strawberry.field(description="Is this alias using SSL? If true, the alias will be accessed via https:// instead of http://. This is used to indicate that the alias is secure and should be accessed via SSL")
    challenge: str = strawberry.field(description="The challenge of the alias. This is used to verify that the alias is reachable. If set, the alias will be accessed via the challenge URL (e.g. 'example.com/.well-known/challenge'). If not set, the alias will be accessed via the instance's URL.")
    usages: list["ManagementUsedAlias"] = strawberry_django.field(description="The usages of this alias by clients.")


@strawberry_django.type(
    fakts_models.ServiceInstanceMapping,
    filters=filters.ServiceInstanceMappingFilter,
    pagination=True,
    description="A ServiceInstance is a configured instance of a Service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information.",
)
class ManagementServiceInstanceMapping:
    id: strawberry.ID
    instance: ManagementServiceInstance = strawberry.field(description="The service that this instance belongs to.")
    client: "ManagementClient" = strawberry.field(description="The client that this instance belongs to.")
    key: str = strawberry.field(description="The key of the instance. This is a unique string that identifies the instance. It is used to identify the instance in the code and in the database.")
    optional: bool = strawberry.field(description="Is this mapping optional? If a mapping is optional, you can configure the client without this mapping.")


@strawberry_django.type(
    fakts_models.App,
    filters=fakts_filters.AppFilter,
    description="An App is the Arkitekt equivalent of a Software Application. It is a collection of `Releases` that can be all part of the same application. E.g the App `Napari` could have the releases `0.1.0` and `0.2.0`.",
    pagination=True,
)
class ManagementApp:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the app")
    identifier: fakts_scalars.AppIdentifier = strawberry.field(description="The identifier of the app. This should be a globally unique string that identifies the app. We encourage you to use the reverse domain name notation. E.g. `com.example.myapp`")

    releases: list["ManagementRelease"] = strawberry.field(description="The releases of the app. A release is a version of the app that can be installed by a user.")

    logo: ManagementMediaStore | None = strawberry.field(description="The logo of the app. This should be a url to a logo that can be used to represent the app.")


@strawberry_django.type(
    fakts_models.Layer,
    description="A Layer is a transport layer that needs to be used to reach an alias. E.g a VPN layer or a Tor layer.",
    pagination=True,
    filters=filters.ManagementLayerFilter,
    order=filters.ManagementLayerOrder,
)
class ManagementLayer:
    id: strawberry.ID

    organization: "ManagementOrganization" = strawberry.field(description="The organization that owns this alias.")
    kind: enums.LayerKind = strawberry.field(description="The kind of the layer. E.g. `VPN` or `TOR`")
    name: str = strawberry.field(description="The name of the layer")
    description: str | None = strawberry.field(description="The description of the layer. This should be a human readable description of the layer.")
    logo: ManagementMediaStore | None = strawberry.field(description="The logo of the layer. This should be a url to a logo that can be used to represent the layer.")
    description: str | None = strawberry.field(description="The description of the service. This should be a human readable description of the service.")
    aliases: list["ManagementInstanceAlias"] = strawberry_django.field(
        description="The instances of the service. A service instance is a configured instance of a service. It will be configured by a configuration backend and will be used to send to the client as a configuration. It should never contain sensitive information."
    )

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return queryset.filter(organization__memberships__user=info.context.request.user).distinct()


@strawberry_django.type(
    fakts_models.Release,
    description="A Release is a version of an app. Releases might change over time. E.g. a release might be updated to fix a bug, and the release might be updated to add a new feature. This is why they are the home for `scopes` and `requirements`, which might change over the release cycle.",
)
class ManagementRelease:
    id: strawberry.ID
    app: ManagementApp = strawberry.field(description="The app that this release belongs to.")
    version: fakts_scalars.Version = strawberry.field(description="The version of the release. This should be a string that identifies the version of the release. We enforce semantic versioning notation. E.g. `0.1.0`. The version is unique per app.")
    name: str = strawberry.field(description="The name of the release. This should be a string that identifies the release beyond the version number. E.g. `canary`.")
    logo: ManagementMediaStore | None = strawberry.field(description="The logo of the release. This should be a url to a logo that can be used to represent the release.")
    scopes: list[str] = strawberry.field(description="The scopes of the release. Scopes are used to limit the access of a client to a user's data. They represent app-level permissions.")
    requirements: list[str] = strawberry.field(description="The requirements of the release. Requirements are used to limit the access of a client to a user's data. They represent app-level permissions.")
    clients: list["ManagementClient"] = strawberry.field(description="The clients of the release")


@strawberry_django.type(
    fakts_models.DeviceGroup,
    description="A DeviceGroup is a group of compute nodes that can be used to run clients. DeviceGroups can be used to group compute nodes by location, hardware type, or any other criteria.",
    pagination=True,
    filters=filters.ManagementDeviceGroupFilter,
    order=filters.ManagementDeviceGroupOrder,
)
class ManagementDeviceGroup:
    id: strawberry.ID
    name: str = strawberry.field(description="The name of the device group.")
    description: str | None = strawberry.field(description="The description of the device group.")

    @strawberry_django.field(description="The number of devices in this device group.")
    def devices(self, info: Info) -> list["ManagementDevice"]:
        return self.compute_nodes.all()

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return queryset.filter(organization__memberships__user=info.context.request.user).distinct()


@strawberry_django.type(fakts_models.ComputeNode, filters=filters.ManagementDeviceFilter, order=filters.ManagementDeviceOrder, pagination=True)
class ManagementDevice:
    id: strawberry.ID
    name: str | None
    node_id: strawberry.ID
    clients: list["ManagementClient"]
    organization: "ManagementOrganization" = strawberry.field(description="The organization that owns this compute node.")
    service_instances: list[ManagementServiceInstance] = strawberry_django.field(description="The service instances that are associated with this compute node.")
    device_groups: list[ManagementDeviceGroup] = strawberry_django.field(description="The device groups that belong to this compute node.")

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return queryset.filter(organization__memberships__user=info.context.request.user).distinct()


@strawberry.type(description="A Public Source is a source of information about a client that is publicly available. E.g. a GitHub repository or a website.")
class ManagementPublicSource:
    kind: str = strawberry.field(description="The kind of the public source. E.g. `github` or `website`.")
    url: str = strawberry.field(description="The url of the public source.")


@strawberry_django.type(fakts_models.UsedAlias, filters=filters.ManagementDeviceFilter, pagination=True)
class ManagementUsedAlias:
    id: strawberry.ID
    key: str
    alias: Optional[ManagementInstanceAlias] = strawberry.field(description="The alias that is used.")
    client: "ManagementClient" = strawberry.field(description="The client that is using the alias.")
    valid: bool = strawberry.field(description="Is the alias valid for the client?")
    reason: Optional[str] = strawberry.field(description="If the alias is not valid, the reason why it is not valid.")


@strawberry_django.type(
    fakts_models.Client,
    description="""A client is a way of authenticating users with a release.
 The strategy of authentication is defined by the kind of client. And allows for different authentication flow. 
 E.g a client can be a DESKTOP app, that might be used by multiple users, or a WEBSITE that wants to connect to a user's account, 
 but also a DEVELOPMENT client that is used by a developer to test the app. The client model thinly wraps the oauth2 client model, which is used to authenticate users.""",
    filters=filters.ManagementClientFilter,
    order=filters.ManagementClientOrder,
    pagination=True,
)
class ManagementClient:
    id: strawberry.ID
    functional: bool = strawberry_django.field(description="Is this client functional? A non-functional client cannot be used to authenticate users.")
    release: ManagementRelease = strawberry_django.field(description="The release that this client belongs to.")
    kind: str = strawberry_django.field(description="The kind of the client. The kind defines the authentication flow that is used to authenticate users with this client.")
    public: bool = strawberry_django.field(description="Is this client public? If a client is public ")
    user: ManagementUser | None = strawberry_django.field(description="If the client is a DEVELOPMENT client, which requires no further authentication, this is the user that is authenticated with the client.")
    organization: ManagementOrganization = strawberry_django.field(description="The client")
    logo: ManagementMediaStore | None = strawberry_django.field(description="The logo of the release. This should be a url to a logo that can be used to represent the release.")
    name: str = strawberry_django.field(description="The name of the client. This is a human readable name of the client.")
    mappings: list["ManagementServiceInstanceMapping"] = strawberry_django.field(description="The mappings of the client. A mapping is a mapping of a service to a service instance. This is used to configure the composition.")
    used_aliases: list[ManagementUsedAlias] = strawberry_django.field(description="The aliases that are used by this client.")
    last_reported_at: datetime.datetime | None = strawberry_django.field(description="The last time the client reported in. This is used to determine if the client is active or not.")
    scopes: list["ManagementScope"] = strawberry.django.field(description="The scopes that are granted to this client.")

    @strawberry_django.field(description="Check if the device code is still valid")
    def manifest(self, info: Info) -> ManagementStagingManifest:
        if not self.manifest:
            return None

        return base_models.Manifest(**self.manifest)

    @strawberry.field(description="The configuration of the client. This is the configuration that will be sent to the client. It should never contain sensitive information.")
    def token(self, info) -> str:
        # TODO: Implement only tenant should be able to see the token
        return self.token

    @strawberry_django.field(description="The issue url of the client. This is the url where users can report issues and get more information about the client.")
    def issue_url(self, info) -> str | None:
        for source in self.public_sources:
            print(source)
            if source.get("kind").lower() == "github":
                return source.get("url") + "/issues/new"

        return None

    @strawberry_django.field(description="The public sources of the client. These are the public sources where users can find more information about the client.")
    def public_sources(self, info) -> list[ManagementPublicSource]:
        sources = []
        for source in self.public_sources:
            sources.append(
                ManagementPublicSource(
                    kind=source.get("kind"),
                    url=source.get("url"),
                )
            )
        return sources

    @strawberry_django.field(description="Check if the client is active")
    def device(self, info) -> Optional["ManagementDevice"]:
        return self.node

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return queryset.filter(organization__memberships__user=info.context.request.user).distinct()


@strawberry_django.type(fakts_models.DeviceCode, filters=karakter_filters.OrganizationFilter, pagination=True, description="""An Organization is a group of users that can work together on a project.""")
class ManagementDeviceCode:
    id: strawberry.ID
    user: Optional[ManagementUser]
    created_at: datetime.datetime
    expires_at: datetime.datetime
    code: str
    client: Optional[ManagementClient]
    staging_kind: str
    denied: bool

    @strawberry_django.field(description="Check if the device code is still valid")
    def staging_manifest(self, info: Info) -> Optional[ManagementStagingManifest]:
        if not self.staging_manifest:
            return None
        return ManagementStagingManifest(**self.staging_manifest)


@strawberry_django.type(fakts_models.ServiceDeviceCode, filters=karakter_filters.OrganizationFilter, pagination=True, description="""An Organization is a group of users that can work together on a project.""")
class ManagementServiceDeviceCode:
    id: strawberry.ID
    user: Optional[ManagementUser]
    created_at: datetime.datetime
    expires_at: datetime.datetime
    code: str
    instance: Optional[ManagementServiceInstance]
    staging_kind: str
    denied: bool

    @strawberry_django.field(description="Check if the device code is still valid")
    def staging_manifest(self, info: Info) -> Optional[ManagementStagingServiceManifest]:
        if not self.staging_manifest:
            return None

        return base_models.ServiceManifest(**self.staging_manifest)

    @strawberry_django.field(description="The instance that this device code is for.")
    def staging_aliases(self, info: Info) -> Optional[List[StagingAlias]]:
        return [
            StagingAlias(
                **alias,
            )
            for alias in self.staging_aliases
        ]


@strawberry_django.type(fakts_models.CompositionDeviceCode, filters=karakter_filters.OrganizationFilter, pagination=True, description="""An Organization is a group of users that can work together on a project.""")
class ManagementCompositionDeviceCode:
    id: strawberry.ID
    user: Optional[ManagementUser]
    created_at: datetime.datetime
    expires_at: datetime.datetime
    code: str
    composition: Optional[ManagementComposition]
    staging_kind: str
    denied: bool

    @strawberry_django.field(description="Check if the device code is still valid")
    def manifest(self, info: Info) -> Optional[ManagementCompositionManifest]:
        if not self.manifest:
            return None

        return base_models.CompositionManifest(**self.manifest)


@strawberry_django.type(fakts_models.RedeemToken, pagination=True)
class ManagementRedeemToken:
    id: strawberry.ID
    token: str = strawberry.field(description="The token of the redeem token")
    client: ManagementClient | None = strawberry.field(description="The client that this redeem token belongs to.")
    user: ManagementUser = strawberry.field(description="The user that this redeem token belongs to.")

    def get_queryset(cls, info) -> fakts_models.RedeemToken:
        return fakts_models.RedeemToken.objects.filter(user=info.context.request.user, organization=info.context.request.organization)
