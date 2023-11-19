import strawberry_django
from karakter import models, scalars, enums, filters
import strawberry
from enum import Enum
from typing import Optional, List, cast
from typing import Any, Dict
from typing import ForwardRef
from strawberry import LazyType
import datetime
from allauth.socialaccount import models as smodels
from ekke.types import Info


@strawberry_django.type(models.Group, filters=filters.GroupFilter, pagination=True)
class Group:
    id: strawberry.ID
    name: str
    users: list['User']



def cast_to_model(model: smodels.SocialAccount):
    print(model.provider)
    if model.provider == "orcid":
        print("Matching?")
        return cast(OrcidAccount, model)
    else:
        return cast(GenericAccount, model)




@strawberry_django.type(models.User, filters=filters.UserFilter, pagination=True)
class User:
    id: strawberry.ID
    username: str
    first_name: str | None
    last_name: str | None
    email: str | None
    groups: list[Group]
    avatar: str | None

    @strawberry_django.field()
    def social_accounts(self, info) -> list["SocialAccount"]:
        return list(smodels.SocialAccount.objects.filter(user=self))
    


@strawberry_django.interface(smodels.SocialAccount)
class SocialAccount:
    provider: str 
    uid: str
    extra_data: scalars.ExtraData

@strawberry.type()
class OrcidIdentifier:
    uri: str 
    path: str 
    host: str

@strawberry.type()
class OrcidPreferences:
    locale: str

@strawberry.type()
class OrcidResearcherURLS:
    path: str
    urls: list[str]

@strawberry.type()
class OrcidAddresses:
    path: str
    addresses: list[str]

@strawberry.type()
class OrcidPerson():
    researcher_urls: list[str]
    addresses: list[str]


@strawberry.type()
class OrcidActivities:
    educations: list[str]


@strawberry_django.type(smodels.SocialAccount, filters=filters.SocialAccountFilter, pagination=True)
class OrcidAccount(SocialAccount):

    @strawberry_django.field()
    def identifier(self) -> OrcidIdentifier:
        return OrcidIdentifier(**self.extra_data["orcid-identifier"])
    
    @strawberry_django.field()
    def person(self) -> Optional[OrcidPerson]:

        person = self.extra_data.get("person", None)
        if not person: return None

        researcher_urls = self.extra_data.get("researcher-urls", {}).get("researcher-urls", [])
        addresses = self.extra_data.get("addresses", {}).get("addresses", [])



        return OrcidPerson(researcher_urls=researcher_urls, addresses=addresses)
    
    @staticmethod
    def is_type_of(ob, info):
        return ob.provider == "orcid"
    
@strawberry_django.type(smodels.SocialAccount)
class GithubAccount(SocialAccount):

    @strawberry_django.field()
    def identifier(self) -> OrcidIdentifier:
        return OrcidIdentifier(**self.extra_data["orcid-identifier"])
    
    @staticmethod
    def is_type_of(ob, info):
        return ob.provider == "github"


@strawberry_django.type(smodels.SocialAccount)
class GenericAccount(SocialAccount):
    extra_data: scalars.ExtraData

    @staticmethod
    def is_type_of(ob, info):
        return ob.provider != "orcid"



@strawberry.type()
class Communication:
    channel: strawberry.ID
