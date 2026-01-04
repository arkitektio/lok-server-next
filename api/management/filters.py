import strawberry
import strawberry_django
from fakts import models as fakts_models


@strawberry_django.filter(fakts_models.ComputeNode)
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


@strawberry_django.order(fakts_models.Client)
class ManagementClientOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry_django.filter(fakts_models.Client)
class ManagementClientFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    functional: bool | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_functional(self, queryset, info):
        if self.functional is None:
            return queryset
        return queryset.filter(functional=self.functional)


@strawberry_django.order(fakts_models.InstanceAlias)
class ManagementInstanceAliasOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry_django.filter(fakts_models.InstanceAlias)
class ManagementInstanceAliasFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    functional: bool | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_functional(self, queryset, info):
        if self.functional is None:
            return queryset
        return queryset.filter(functional=self.functional)


@strawberry_django.filter(fakts_models.ServiceInstanceMapping)
class ServiceInstanceMappingFilter:
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
