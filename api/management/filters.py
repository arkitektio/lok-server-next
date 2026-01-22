import strawberry
import strawberry_django
from fakts import models as fakts_models
from allauth.socialaccount import models as smodels
from karakter import models as karakter_models


@strawberry_django.order(fakts_models.KommunityPartner)
class ManagementKommunityPartnerOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    last_reported_at: strawberry.auto


@strawberry_django.filter(fakts_models.KommunityPartner)
class ManagementKommunityPartnerFilter:
    search: str | None = None
    ids: list[strawberry.ID] | None = None
    auto_configure: bool | None = None
    applicable_for_me: bool | None = None
    has_preconfigured_composition: bool | None = None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__icontains=self.search)

    def filter_auto_configure(self, queryset, info):
        if self.auto_configure is None:
            return queryset
        return queryset.filter(auto_configure=self.auto_configure)

    def filter_has_preconfigured_composition(self, queryset, info):
        if self.has_preconfigured_composition is None:
            return queryset
        if self.has_preconfigured_composition:
            return queryset.exclude(preconfigured_composition__isnull=True).exclude(preconfigured_composition={})
        return queryset.filter(preconfigured_composition__isnull=True) | queryset.filter(preconfigured_composition={})

    def filter_applicable_for_me(self, queryset, info):
        """Filter partners that apply to the current user based on their filter_config."""
        if self.applicable_for_me is None:
            return queryset
        
        user = info.context.request.user
        if not user.is_authenticated:
            return queryset.none() if self.applicable_for_me else queryset
        
        # We need to filter in Python since filter_config logic is complex
        applicable_ids = []
        for partner in queryset:
            if partner.applies_to_user(user) == self.applicable_for_me:
                applicable_ids.append(partner.id)
        
        return queryset.filter(id__in=applicable_ids)


@strawberry_django.order(fakts_models.IonscaleLayer)
class ManagementLayerOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    last_reported_at: strawberry.auto


@strawberry_django.filter(fakts_models.IonscaleLayer)
class ManagementLayerFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(fakts_models.DeviceGroup)
class ManagementDeviceGroupOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    last_reported_at: strawberry.auto


@strawberry_django.filter(fakts_models.DeviceGroup)
class ManagementDeviceGroupFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(fakts_models.Composition)
class ManagementCompositionOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    last_reported_at: strawberry.auto


@strawberry_django.filter(fakts_models.Composition)
class ManagementCompositionFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(fakts_models.ComputeNode)
class ManagementDeviceOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    last_reported_at: strawberry.auto


@strawberry_django.filter(fakts_models.ComputeNode)
class ManagementDeviceFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(karakter_models.Membership)
class ManagementMembershipOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    last_reported_at: strawberry.auto


@strawberry_django.filter(karakter_models.Membership)
class ManagementMembershipFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(fakts_models.Client)
class ManagementClientOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    last_reported_at: strawberry.auto


@strawberry_django.filter(fakts_models.Client)
class ManagementClientFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    functional: bool | None
    organization: strawberry.ID | None

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

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


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


@strawberry_django.order(fakts_models.ServiceInstanceMapping)
class ManagementServiceInstanceMappingOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry_django.filter(fakts_models.ServiceInstanceMapping)
class ServiceInstanceMappingFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(fakts_models.ServiceInstance)
class ManagementServiceInstanceOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry_django.filter(fakts_models.ServiceInstance)
class ManagementServiceInstanceFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(smodels.SocialAccount)
class ManagementSocialAccountOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry_django.filter(smodels.SocialAccount)
class ManagementSocialAccountFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)


@strawberry_django.order(karakter_models.Role)
class ManagementRoleOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry_django.filter(karakter_models.Role)
class ManagementRoleFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None
    creating_instance: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)

    def filter_creating_instance(self, queryset, info):
        if self.creating_instance is None:
            return queryset
        return queryset.filter(creating_instance__id=self.creating_instance)


@strawberry_django.order(karakter_models.Scope)
class ManagementScopeOrder:
    name: strawberry.auto
    created_at: strawberry.auto
    updated_at: strawberry.auto


@strawberry_django.filter(karakter_models.Scope)
class ManagementScopeFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    organization: strawberry.ID | None
    creating_instance: strawberry.ID | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(name__contains=self.search)

    def filter_organization(self, queryset, info):
        if self.organization is None:
            return queryset
        return queryset.filter(organization__id=self.organization)

    def filter_creating_instance(self, queryset, info):
        if self.creating_instance is None:
            return queryset
        return queryset.filter(creating_instance__id=self.creating_instance)


@strawberry_django.order(fakts_models.IonscaleAuthKey)
class ManagementIonscaleAuthKeyOrder:
    created_at: strawberry.auto
    ephemeral: strawberry.auto


@strawberry_django.filter(fakts_models.IonscaleAuthKey)
class ManagementIonscaleAuthKeyFilter:
    search: str | None
    ids: list[strawberry.ID] | None
    layer: strawberry.ID | None
    ephemeral: bool | None

    def filter_ids(self, queryset, info):
        if self.ids is None:
            return queryset
        return queryset.filter(id__in=self.ids)

    def filter_search(self, queryset, info):
        if self.search is None:
            return queryset
        return queryset.filter(key__contains=self.search)

    def filter_layer(self, queryset, info):
        if self.layer is None:
            return queryset
        return queryset.filter(layer__id=self.layer)

    def filter_ephemeral(self, queryset, info):
        if self.ephemeral is None:
            return queryset
        return queryset.filter(ephemeral=self.ephemeral)
