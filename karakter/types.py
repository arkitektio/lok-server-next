import strawberry_django
from karakter import models, scalars, enums, filters
import strawberry
from enum import Enum
from typing import Optional
from typing import Any, Dict
from typing import ForwardRef
from strawberry import LazyType
from typing import Literal, Union
import datetime

@strawberry_django.type(models.Group, filters=filters.GroupFilter, pagination=True)
class Group:
    id: strawberry.ID
    name: str
    users: list['User']



@strawberry_django.type(models.User, filters=filters.UserFilter, pagination=True)
class User:
    id: strawberry.ID
    username: str
    first_name: str | None
    last_name: str | None
    email: str | None
    groups: list[Group]
    avatar: str | None


@strawberry.type()
class Communication:
    channel: strawberry.ID
