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


class ClientRoleChoices(TextChoices):
    """The operational role of a client, orthogonal to its kind (auth flow)."""

    INTERFACE = "interface", "INTERFACE (Value represent INTERFACE)"
    AGENT = "agent", "AGENT (Value represent AGENT)"


class ClientRoleVanilla(str, Enum):
    INTERFACE = "interface"
    AGENT = "agent"


@strawberry.enum
class ClientRole(str, Enum):
    INTERFACE = strawberry.enum_value(
        "interface",
        description="""An interface client. Interface clients are human interfaces: a user actively
operates them (clicking through a UI, running a desktop app, browsing a website). They represent a
person interacting with the platform in real time.""",
    )
    AGENT = strawberry.enum_value(
        "agent",
        description="""An agent client. Agent clients are authorized once by a user and then run
unattended, receiving and processing tasks on that user's behalf (e.g. a Rekuest worker). They act
automatically rather than being driven by a human in real time.""",
    )


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
    