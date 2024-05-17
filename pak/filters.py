import strawberry
from pak import models, enums
from strawberry import auto
from typing import Optional
from strawberry_django.filters import FilterLookup
import strawberry_django

@strawberry_django.filter(models.StashItem)
class StashItemFilter:
    search: str | None
    username: Optional[FilterLookup[str]] | None
    ids: list[strawberry.ID] | None
    stashes: Optional[list[strawberry.ID]] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(username__contains=self.search)
    
    def filter_stashes(self, queryset, info):
        if self.stashes is None:
            return queryset
        return queryset.filter(stashes__in=self.stashes)


@strawberry_django.filter(models.Stash, description="__doc__")
class StashFilter:
    """ A Filterset to Filter Groups """
    search: str | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)
    

