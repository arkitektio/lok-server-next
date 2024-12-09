import strawberry_django
from pak import models, enums, filters
import strawberry
from enum import Enum
from typing import Optional, List, cast
from typing import Any, Dict
from typing import ForwardRef
from strawberry import LazyType
import datetime
from karakter.types import User
from ekke.types import Info


@strawberry_django.type(
    models.StashItem,
    filters=filters.StashItemFilter,
    pagination=True,
    description="""
A stashed item
""",
)
class StashItem:
    id: strawberry.ID
    identifier: str
    description: str | None
    object: str
    added_at: datetime.datetime
    updated_at: datetime.datetime


@strawberry_django.type(
    models.Stash,
    filters=filters.StashFilter,
    pagination=True,
    description="""
A Stash
""",
)
class Stash:
    id: strawberry.ID
    name: str
    description: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_active: bool

    items: list["StashItem"]

    @strawberry.field(description="The number of items in the stash")
    def owner(self, info: Info) -> User:
        return self.owner
