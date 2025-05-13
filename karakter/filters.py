import strawberry
from karakter import models, scalars, enums
from strawberry import auto
from typing import Optional
from strawberry_django.filters import FilterLookup
import strawberry_django


@strawberry_django.filter(models.User)
class UserFilter:
    search: str | None
    username: Optional[FilterLookup[str]] | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(username__contains=self.search)


@strawberry_django.filter(models.Group, description="__doc__")
class GroupFilter:
    """A Filterset to Filter Groups"""

    search: str | None
    name: Optional[FilterLookup[str]] | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)


@strawberry_django.filter(models.Profile)
class ProfileFilter:
    search: str | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(bio__contains=self.search)


@strawberry_django.filter(models.Profile)
class GroupProfileFilter:
    search: str | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(bio__contains=self.search)




