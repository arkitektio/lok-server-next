from enum import Enum
import strawberry
from django.db.models import TextChoices


class LayerKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    WEB = "public", "WEB (Value represent WEB)"
    TAILSCALE = "tailscale", "TAILSCALE (Value represent TAILSCALE)"
    VPN = "vpn", "VPN (Value represent VPN)"
    DOCKER = "docker", "DOCKER (Value represent DOCKER)"


class AliasKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    ABSOLUTE = "absolute", "ABSOLUTE (Value represent ABSOLUTE)"
    RELATIVE = "relative", "RELATIVE (Value represent RELATIVE)"


class ClientKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    WEBSITE = "website", "WEBSITE (Value represent WEBSITE)"
    DEVELOPMENT = "development", "DEVELOPMENT (Value represent DEVELOPMENT)"
    DESKTOP = "desktop", "DESKTOP (Value represent DESKTOP Aüü)"


class ClientKindVanilla(str, Enum):
    WEBSITE = "website"
    DEVELOPMENT = "development"
    DESKTOP = "desktop"


@strawberry.enum
class FaktValueType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


@strawberry.enum
class ClientKind(str, Enum):
    DEVELOPMENT = strawberry.enum_value(
        "development",
        description="A development client. Development clients are clients that receive a client_id and client_secret, and are always linked to a user, that grants rights when creating the application. There is no active user authentication when the app gets started. They are used for development purposes.",
    )
    WEBSITE = strawberry.enum_value(
        "website",
        description="""A website clients. Website clients need to undergo an authentication flow, where the user is redirected to the website, before the client can be used. They are used for website applications, that want to access a user's data, and are hosted on non trusted domains.""",
    )
    DESKTOP = strawberry.enum_value(
        "desktop",
        description="""A desktop client. Desktop clients need to undergo an authentication flow, where the user is redirect back to the application. They use redirect but only on loopback adapters.""",
    )


class FilterKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    HOST_REGEX = "host_regex", "Host matches regex"
    HOST_IS = "host_is", "Host is"
    HOST_IS_NOT = "host_is_not", "Host is not"
    PORT_IS = "port_is", "Port is"
    PORT_IS_NOT = "port_is_not", "Port is not"
    VERSION_IS = "version_is", "Version is"
    VERSION_IS_NOT = "version_is_not", "Version is not"
    VERSION_REGEX = "version_regex", "Version matches regex"
    IDENTIFIER_IS = "identifier_is", "Identifier is"
    IDENTIFIER_IS_NOT = "identifier_is_not", "Identifier is not"
    IDENTIFIER_REGEX = "identifier_regex", "Identifier matches regex"
    USER_IS = "user_is", "Checks if user is certain id"
    USER_IS_DEVELOPER = "user_is_developer", "Checks if the user is developer"


@strawberry.enum
class FilterKind(str, Enum):
    HOST_REGEX = "host_regex"
    HOST_IS = "host_is"
    HOST_IS_NOT = "host_is_not"
    PORT_IS = "port_is"
    PORT_IS_NOT = "port_is_not"
    VERSION_IS = "version_is"
    VERSION_IS_NOT = "version_is_not"
    VERSION_REGEX = "version_regex"
    IDENTIFIER_IS = "identifier_is"
    IDENTIFIER_IS_NOT = "identifier_is_not"
    IDENTIFIER_REGEX = "identifier_regex"
    USER_IS = "user_is"
    USER_IS_DEVELOPER = "user_is_developer"
    
    
@strawberry.enum
class InstancePermissionKind(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


class FaktsGrantKindChoices(TextChoices):
    """Event Type for the Event Operator"""

    RETRIEVE = "retrieve", "RETRIEVE (Value represent RETRIEVE)"
    DEVICE_CODE = "device_code", "DEVICE_CODE (Value represent DEVICE_CODE)"


@strawberry.enum
class FaktsGrantKind(str, Enum):
    RETRIEVE = "retrieve"
    DEVICE_CODE = "device_code"



@strawberry.enum
class KommunityKind(str, Enum):
    OPEN = "open"
    RESTRICTED = "restricted"
    PRIVATE = "private"
    
    
@strawberry.enum
class PartnerKind(str, Enum):
    PREAUTHORIZED = "preauthorized"
    OAUTH_FLOW = "oauth2"
    