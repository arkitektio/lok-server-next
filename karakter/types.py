import datetime
from enum import Enum
from typing import Any, Dict, ForwardRef, List, Optional, cast
from karakter.datalayer import get_current_datalayer
import strawberry
import strawberry_django
from allauth.socialaccount import models as smodels
from ekke.types import Info
from karakter import enums, filters, models, scalars
from strawberry import LazyType


@strawberry_django.type(
    models.Group,
    filters=filters.GroupFilter,
    pagination=True,
    description="""
A Group is the base unit of Role Based Access Control. A Group can have many users and many permissions. A user can have many groups. A user with a group that has a permission can perform the action that the permission allows.
Groups are propagated to the respecting subservices. Permissions are not. Each subservice has to define its own permissions and mappings to groups.
""",
)
class Group:
    id: strawberry.ID
    name: str
    profile: Optional["GroupProfile"] 
    
    @strawberry_django.field(description="The users that are in the group")
    def users(self, info: Info) -> List["User"]:
        return models.User.objects.filter(groups=self)
    
    
  
  

@strawberry_django.type(models.MediaStore)
class MediaStore:
    id: strawberry.ID
    path: str
    bucket: str
    key: str

    @strawberry_django.field()
    def presigned_url(self, info: Info, host: str | None = None) -> str:
        datalayer = get_current_datalayer()
        return cast(models.MediaStore, self).get_presigned_url(
            info, datalayer=datalayer, host=host
        )
  


def cast_to_model(model: smodels.SocialAccount):
    print(model.provider)
    if model.provider == "orcid":
        print("Matching?")
        return cast(OrcidAccount, model)
    else:
        return cast(GenericAccount, model)


@strawberry_django.type(
    models.User,
    filters=filters.UserFilter,
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
class User:
    id: strawberry.ID
    username: str
    first_name: str | None
    last_name: str | None
    email: str | None
    groups: list[Group]
    avatar: str | None
    profile: "Profile"
    managed_clients: strawberry.auto

    @strawberry_django.field()
    def social_accounts(self, info) -> list["SocialAccount"]:
        return list(smodels.SocialAccount.objects.filter(user=self))

    

@strawberry_django.type(
    models.Profile,
    filters=filters.ProfileFilter,
    pagination=True,
    description="""
A Profile of a User. A Profile can be used to display personalied information about a user.

""",
)
class Profile:
    id: strawberry.ID
    bio: str | None = strawberry.field(description="A short bio of the user")
    name: str | None  = strawberry.field(description="The name of the user")
    avatar: MediaStore | None = strawberry.field(description="The avatar of the user")


@strawberry_django.type(
    models.GroupProfile,
    filters=filters.GroupProfileFilter,
    pagination=True,
    description="""
A Profile of a User. A Profile can be used to display personalied information about a user.




""",
)
class GroupProfile:
    id: strawberry.ID
    bio: str | None  = strawberry.field(description="A short bio of the group")
    name: str | None  = strawberry.field(description="The name of the group")
    avatar: MediaStore | None = strawberry.field(description="The avatar of the group")
    

@strawberry_django.interface(
    smodels.SocialAccount,
    description="""
A Social Account is an account that is associated with a user. It can be used to authenticate the user with external services. It
can be used to store extra data about the user that is specific to the provider. We provide typed access to the extra data for
some providers. For others we provide a generic json field that can be used to store arbitrary data. Generic accounts are
always available, but typed accounts are only available for some providers.
""",
)
class SocialAccount:
    provider: enums.ProviderType = strawberry.field(
        description="The provider of the account. This can be used to determine the type of the account."
    )
    uid: str = strawberry.field(
        description="The unique identifier of the account. This is unique for the provider."
    )
    extra_data: scalars.ExtraData = strawberry.field(
        description="Extra data that is specific to the provider. This is a json field and can be used to store arbitrary data."
    )


@strawberry.type(
    description="""The ORCID Identifier of a user. This is a unique identifier that is used to identify a user on the ORCID service. It is composed of a uri, a path and a host."""
)
class OrcidIdentifier:
    uri: str = strawberry.field(description="The uri of the identifier")
    path: str = strawberry.field(description="The path of the identifier")
    host: str = strawberry.field(description="The host of the identifier")


@strawberry.type(
    description="""The ORCID Preferences of a user. This is a set of preferences that are specific to the ORCID service. Currently only the locale is supported."""
)
class OrcidPreferences:
    locale: str = strawberry.field(
        description="The locale of the user. This is used to determine the language of the ORCID service."
    )


@strawberry.type(description="""Assoiated OridReseracher Result""")
class OrcidResearcherURLS:
    path: str
    urls: list[str]


@strawberry.type()
class OrcidAddresses:
    path: str
    addresses: list[str]


@strawberry.type()
class OrcidPerson:
    researcher_urls: list[str]
    addresses: list[str]


@strawberry.type()
class OrcidActivities:
    educations: list[str]


@strawberry_django.type(
    smodels.SocialAccount,
    filters=filters.SocialAccountFilter,
    pagination=True,
    description="""
An ORCID Account is a Social Account that maps to an ORCID Account. It provides information about the
user that is specific to the ORCID service. This includes the ORCID Identifier, the ORCID Preferences and
the ORCID Person. The ORCID Person contains information about the user that is specific to the ORCID service.
This includes the ORCID Activities, the ORCID Researcher URLs and the ORCID Addresses.

""",
)
class OrcidAccount(SocialAccount):

    @strawberry_django.field(
        description="The ORCID Identifier of the user. The UID of the account is the same as the path of the identifier."
    )
    def identifier(self) -> OrcidIdentifier:
        return OrcidIdentifier(**self.extra_data["orcid-identifier"])

    @strawberry_django.field(
        description="Information about the person that is specific to the ORCID service."
    )
    def person(self) -> Optional[OrcidPerson]:

        person = self.extra_data.get("person", None)
        if not person:
            return None

        researcher_urls = self.extra_data.get("researcher-urls", {}).get(
            "researcher-urls", []
        )
        addresses = self.extra_data.get("addresses", {}).get("addresses", [])

        return OrcidPerson(researcher_urls=researcher_urls, addresses=addresses)

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider == "orcid"


@strawberry_django.type(
    smodels.SocialAccount,
    filters=filters.SocialAccountFilter,
    pagination=True,
    description="""
The Github Account is a Social Account that maps to a Github Account. It provides information about the
user that is specific to the Github service. This includes the Github Identifier.

""",
)
class GithubAccount(SocialAccount):

    @strawberry_django.field()
    def identifier(self) -> OrcidIdentifier:
        raise NotImplementedError()

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider == "github"


@strawberry_django.type(
    smodels.SocialAccount,
    filters=filters.SocialAccountFilter,
    pagination=True,
    description="""
The Generic Account is a Social Account that maps to a generic account. It provides information about the
user that is specific to the provider. This includes untyped extra data.

""",
)
class GenericAccount(SocialAccount):
    extra_data: scalars.ExtraData

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider != "orcid"


@strawberry.type(description="""A Communication""")
class Communication:
    channel: strawberry.ID


@strawberry_django.type(
    models.SystemMessage,
    filters=filters.ProfileFilter,
    pagination=True,
    description="""
A System Message is a message that is sent to a user. 
It can be used to notify the user of important events or to request their attention.
System messages can use Rekuest Hooks as actions to allow the user to interact with the message.


""",
)
class SystemMessage:
    id: strawberry.ID
    title: str
    message: str
    action: str
    user: User
