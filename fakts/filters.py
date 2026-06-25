import strawberry
from karakter import models
from typing import Optional
from strawberry_django.filters import FilterLookup
import strawberry_django
from fakts import models as fakts_models
from fakts import enums as fakts_enums


@strawberry_django.filter_type(models.User, description="Filter for User model.")
class UserFilter:
    """Filter for User model."""

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
        return queryset.filter(username__contains=self.search)


@strawberry_django.filter_type(models.Group, description="Filter for Group model.")
class GroupFilter:
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


@strawberry_django.filter_type(fakts_models.Client)
class ClientFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    role: fakts_enums.ClientRole | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_role(self, queryset, info):
        if self.role is None:
            return queryset
        return queryset.filter(role=self.role.value)


@strawberry_django.filter_type(fakts_models.App)
class AppFilter:
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


@strawberry_django.filter_type(fakts_models.RedeemToken)
class RedeemTokenFilter:
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


@strawberry_django.filter_type(fakts_models.Service)
class ServiceFilter:
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


@strawberry_django.filter_type(fakts_models.Device)
class DeviceFilter:
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


@strawberry_django.filter_type(fakts_models.DeviceGroup)
class DeviceGroupFilter:
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


@strawberry_django.filter_type(fakts_models.Layer)
class LayerFilter:
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


@strawberry_django.filter_type(fakts_models.ServiceInstance)
class ServiceInstanceFilter:
    search: str | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(backend__contains=self.search)


@strawberry_django.filter_type(fakts_models.ServiceRelease)
class ServiceReleaseFilter:
    search: str | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(backend__contains=self.search)


@strawberry_django.filter_type(fakts_models.Composition)
class CompositionFilter:
    search: str | None
    ids: list[strawberry.ID] | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(backend__contains=self.search)