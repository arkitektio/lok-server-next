from allauth.socialaccount.providers import registry
import strawberry
from enum import Enum

params = dict(map(lambda x: (x[0].upper(), x[0]), registry.as_choices()))
ManagementProviderKind = strawberry.enum(Enum("ManagementProviderKind", params))
