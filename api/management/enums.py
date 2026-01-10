from allauth.socialaccount.providers import registry
import strawberry
from enum import Enum


params = dict(map(lambda x: (x[0].upper(), x[0]), registry.as_choices()))
ManagementProviderKind = strawberry.enum(Enum("ManagementProviderKind", params))


@strawberry.enum
class LayerKind(str, Enum):
    """Defines the different kinds of layers available in the system."""

    BASE = "base"
    TAILNET = "tailnet"
    IONSCALE = "ionscale"
    VPN = "vpn"
