from typing import Any, AsyncGenerator, Type
from fakts.logic import find_instance_for_requirement, find_instance_for_requirement_and_organization
import strawberry
import strawberry_django
from kante.types import Info
from .types import ManagementOrganization, ManagementUser
import api.management.mutations as mutations
import api.management.types as types
import kante
from karakter import models as karakter_models
from fakts import models as fakts_models
from .datalayer import DatalayerExtension
from allauth.socialaccount import models as smodels
from authapp.models import OAuth2Client


@strawberry.type
class Query:
    organizations: list[types.ManagementOrganization] = kante.django_field()
    friends: list[types.ManagementUser] = kante.django_field()
    apps: list[types.ManagementApp] = kante.django_field()
    releases: list[types.ManagementRelease] = kante.django_field()
    services: list[types.ManagementService] = kante.django_field()
    service_instances: list[types.ManagementServiceInstance] = kante.django_field()
    service_instance_mappings: list[types.ManagementServiceInstanceMapping] = kante.django_field()
    clients: list[types.ManagementClient] = kante.django_field()
    devices: list[types.ManagementDevice] = kante.django_field()
    redeem_tokens: list[types.ManagementRedeemToken] = kante.django_field()
    layers: list[types.ManagementLayer] = kante.django_field()
    device_groups: list[types.ManagementDeviceGroup] = kante.django_field()
    used_aliases: list[types.ManagementUsedAlias] = kante.django_field()
    service_releases: list[types.ManagementServiceRelease] = kante.django_field()
    instance_aliases: list[types.ManagementInstanceAlias] = kante.django_field()
    social_accounts: list[types.ManagementSocialAccount] = kante.django_field()
    memberships: list[types.ManagementMembership] = kante.django_field()
    scopes: list[types.ManagementScope] = kante.django_field()
    roles: list[types.ManagementRole] = kante.django_field()
    compositions: list[types.ManagementComposition] = kante.django_field()
    management_layers: list[types.ManagementLayer] = kante.django_field()

    @kante.django_field()
    def social_account(self, info: Info, id: strawberry.ID) -> types.ManagementSocialAccount:
        return smodels.SocialAccount.objects.get(id=id)

    @kante.django_field()
    def me(self, info: Info) -> ManagementUser:
        return info.context.request.user

    @kante.django_field()
    def role(self, info: Info, id: strawberry.ID) -> types.ManagementRole:
        return karakter_models.Role.objects.get(id=id)


    @kante.django_field()
    def membership(self, info: Info, id: strawberry.ID) -> types.ManagementMembership:
        return karakter_models.Membership.objects.get(id=id)

    @kante.django_field()
    def scope(self, info: Info, id: strawberry.ID) -> types.ManagementScope:
        return karakter_models.Scope.objects.get(id=id)

    @kante.django_field()
    def organization(self, info: Info, id: strawberry.ID) -> types.ManagementOrganization:
        return karakter_models.Organization.objects.get(id=id)

    @kante.django_field()
    def used_alias(self, info: Info, id: strawberry.ID) -> types.ManagementUsedAlias:
        return fakts_models.UsedAlias.objects.get(id=id)

    @kante.django_field()
    def instance_alias(self, info: Info, id: strawberry.ID) -> types.ManagementInstanceAlias:
        return fakts_models.InstanceAlias.objects.get(id=id)

    @kante.django_field(name="service")
    def _service(self, info: Info, id: strawberry.ID) -> types.ManagementService:
        return fakts_models.Service.objects.get(id=id)

    @kante.django_field()
    def app(self, info: Info, id: strawberry.ID) -> types.ManagementApp:
        return fakts_models.App.objects.get(id=id)

    @kante.django_field()
    def service_instance(self, info: Info, id: strawberry.ID) -> types.ManagementServiceInstance:
        return fakts_models.ServiceInstance.objects.get(id=id)

    @kante.django_field()
    def composition(self, info: Info, id: strawberry.ID) -> types.ManagementComposition:
        return fakts_models.Composition.objects.get(id=id)

    @kante.django_field()
    def oauth2_client_by_client_id(self, info: Info, client_id: str) -> types.ManagementOAuth2Client:
        return OAuth2Client.objects.get(client_id=client_id)

    @kante.django_field()
    def validate_device_code(self, info: Info, device_code: strawberry.ID, organization: strawberry.ID) -> types.ValidationResult:
        device_code_obj = fakts_models.DeviceCode.objects.get(id=device_code)
        organization_obj = karakter_models.Organization.objects.get(id=organization)
        user = info.context.request.user
        manifest = device_code_obj.manifest_as_model
        errors: list[str] = []

        mappings: list[types.PotentialMapping] = []

        if not manifest.requirements:
            return types.ValidationResult(valid=True, mappings=[], reason="Manifest has no requirements")

        for req in manifest.requirements:
            try:
                instance = find_instance_for_requirement_and_organization(req, user, organization=organization_obj)
                if instance:
                    mappings.append(
                        types.PotentialMapping(
                            service_instance=instance,
                            key=req.key,
                            reason=None,
                        )
                    )
                else:
                    mappings.append(
                        types.PotentialMapping(
                            service_instance=None,
                            key=req.key,
                            reason=f"No suitable instance found for service {req.service}.",
                        )
                    )
                    if not req.optional:
                        errors.append(f"No suitable instance found for service {req.service}.")
            except Exception as e:
                mappings.append(
                    types.PotentialMapping(
                        service_instance=None,
                        key=req.key,
                        reason=str(e),
                    )
                )

        return types.ValidationResult(
            valid=len(errors) == 0,
            mappings=mappings,
            reason="\n".join(errors) if errors else "All requirements satisfied.",
        )

    @kante.django_field()
    def device_code_by_code(self, info: Info, device_code: str) -> types.ManagementDeviceCode:
        return fakts_models.DeviceCode.objects.get(code=device_code)

    @kante.django_field()
    def invite_by_code(self, info: Info, invite_code: str) -> types.ManagementInvite:
        return karakter_models.Invite.objects.get(token=invite_code)

    @kante.django_field()
    def invite(self, info: Info, id: strawberry.ID) -> types.ManagementInvite:
        invite = karakter_models.Invite.objects.get(id=id)
        assert invite.created_for.owner == info.context.request.user, "Not authorized to view this invite."
        return invite

    @kante.django_field()
    def release(self, info: Info, id: strawberry.ID) -> types.ManagementRelease:
        return fakts_models.Release.objects.get(id=id)

    @kante.django_field()
    def layer(self, info: Info, id: strawberry.ID) -> types.ManagementLayer:
        return fakts_models.IonscaleLayer.objects.get(id=id)

    @kante.django_field()
    def machine(self, info: Info, id: strawberry.ID) -> types.ManagementMachine:
        from ionscale.repo import django_repo
        machine = django_repo.get_machine(str(id))

        if machine.tailnet:
            try:
                layer = fakts_models.IonscaleLayer.objects.get(tailnet_name=machine.tailnet)
                if not layer.organization.memberships.filter(user=info.context.request.user).exists():
                     raise PermissionError("You are not a member of the organization that owns this layer.")
                return types.ManagementMachineDetail(instance=machine, tailnet=machine.tailnet, layer_id=layer.id)
            except fakts_models.IonscaleLayer.DoesNotExist:
                 # What if the machine belongs to a tailnet that is not managed by lok?
                 # For now we fail
                 pass
        
        raise PermissionError("Could not find the layer associated with this machine.")

    @kante.django_field()
    def client(self, info: Info, id: strawberry.ID) -> types.ManagementClient:
        return fakts_models.Client.objects.get(id=id)

    @kante.django_field()
    def service_instance_mapping(self, info: Info, id: strawberry.ID) -> types.ManagementServiceInstanceMapping:
        return fakts_models.ServiceInstanceMapping.objects.get(id=id)

    @kante.django_field()
    def device(self, info: Info, id: strawberry.ID) -> types.ManagementDevice:
        return fakts_models.ComputeNode.objects.get(id=id)

    @kante.django_field()
    def service_release(self, info: Info, id: strawberry.ID) -> types.ManagementServiceRelease:
        return fakts_models.ServiceRelease.objects.get(id=id)

    @kante.django_field()
    def device_group(self, info: Info, id: strawberry.ID) -> types.ManagementDeviceGroup:
        return fakts_models.DeviceGroup.objects.get(id=id)

    @kante.django_field()
    def device_code(self, info: Info, id: strawberry.ID) -> types.ManagementDeviceCode:
        return fakts_models.DeviceCode.objects.get(id=id)

    @kante.django_field()
    def service_device_code(self, info: Info, id: strawberry.ID) -> types.ManagementServiceDeviceCode:
        return fakts_models.ServiceDeviceCode.objects.get(id=id)

    @kante.django_field()
    def service_device_code_by_code(self, info: Info, code: str) -> types.ManagementServiceDeviceCode:
        return fakts_models.ServiceDeviceCode.objects.get(code=code)

    @kante.django_field()
    def composition_device_code(self, info: Info, id: strawberry.ID) -> types.ManagementCompositionDeviceCode:
        return fakts_models.CompositionDeviceCode.objects.get(id=id)

    @kante.django_field()
    def composition_device_code_by_code(self, info: Info, code: str) -> types.ManagementCompositionDeviceCode:
        return fakts_models.CompositionDeviceCode.objects.get(code=code)


@strawberry.type
class Mutation:
    create_organization = strawberry_django.mutation(
        resolver=mutations.create_organization,
    )
    update_organization = strawberry_django.mutation(
        resolver=mutations.update_organization,
    )
    delete_organization = strawberry_django.mutation(
        resolver=mutations.delete_organization,
    )

    create_invite = strawberry_django.mutation(
        resolver=mutations.create_invite,
    )
    accept_invite = strawberry_django.mutation(
        resolver=mutations.accept_invite,
    )
    decline_invite = strawberry_django.mutation(
        resolver=mutations.decline_invite,
        description="Decline an invite to join an organization.",
    )
    cancel_invite = strawberry_django.mutation(
        resolver=mutations.cancel_invite,
    )

    # device Mutations
    create_device = strawberry_django.mutation(
        resolver=mutations.create_device,
    )
    update_device = strawberry_django.mutation(
        resolver=mutations.update_device,
    )
    delete_device = strawberry_django.mutation(
        resolver=mutations.delete_device,
    )

    update_membership = strawberry_django.mutation(
        resolver=mutations.update_membership,
    )
    delete_membership = strawberry_django.mutation(
        resolver=mutations.delete_membership,
    )

    # Compsition Device Code Mutations
    accept_composition_device_code = strawberry_django.mutation(
        resolver=mutations.accept_composition_device_code,
    )
    decline_composition_device_code = strawberry_django.mutation(
        resolver=mutations.decline_composition_device_code,
    )

    # Composition
    update_composition = strawberry_django.mutation(
        resolver=mutations.update_composition,
    )
    delete_composition = strawberry_django.mutation(
        resolver=mutations.delete_composition,
    )

    # Device Code Mutations
    accept_device_code = strawberry_django.mutation(
        resolver=mutations.accept_device_code,
    )
    decline_device_code = strawberry_django.mutation(
        resolver=mutations.decline_device_code,
    )
    # Authorize Connect Mutations
    accept_authorize_code = strawberry_django.mutation(
        resolver=mutations.accept_authorize_code,
    )
    decline_authorize_code = strawberry_django.mutation(
        resolver=mutations.decline_authorize_code,
    )
    # Service Device Code Mutations
    accept_service_device_code = strawberry_django.mutation(
        resolver=mutations.accept_service_device_code,
    )
    decline_service_device_code = strawberry_django.mutation(
        resolver=mutations.decline_service_device_code,
    )

    change_organization_owner = strawberry_django.mutation(
        resolver=mutations.change_organization_owner,
    )

    create_alias = strawberry_django.mutation(
        resolver=mutations.create_alias,
    )
    delete_alias = strawberry_django.mutation(
        resolver=mutations.delete_alias,
    )
    update_alias = strawberry_django.mutation(
        resolver=mutations.update_alias,
    )

    update_profile = strawberry_django.mutation(
        resolver=mutations.update_profile,
    )
    create_profile = strawberry_django.mutation(
        resolver=mutations.create_profile,
    )
    delete_profile = strawberry_django.mutation(
        resolver=mutations.delete_profile,
    )

    update_organization_profile = strawberry_django.mutation(
        resolver=mutations.update_organization_profile,
    )
    create_organization_profile = strawberry_django.mutation(
        resolver=mutations.create_organization_profile,
    )
    delete_organization_profile = strawberry_django.mutation(
        resolver=mutations.delete_organization_profile,
    )

    delete_device_group = strawberry_django.mutation(
        resolver=mutations.delete_device_group,
    )
    create_device_group = strawberry_django.mutation(
        resolver=mutations.create_device_group,
    )
    add_device_to_group = strawberry_django.mutation(
        resolver=mutations.add_device_to_group,
    )

    request_media_upload = strawberry_django.mutation(
        resolver=mutations.request_media_upload,
    )

    create_ionscale_layer = strawberry_django.mutation(
        resolver=mutations.create_ionscale_layer,
    )
    delete_ionscale_layer = strawberry_django.mutation(
        resolver=mutations.delete_ionscale_layer,
    )
    update_ionscale_layer = strawberry_django.mutation(
        resolver=mutations.update_ionscale_layer,
    )


schema = kante.Schema(
    query=Query,
    mutation=Mutation,
    types=[types.ManagementGithubAccount, types.ManagementGenericAccount, types.ManagementGoogleAccount, types.ManagementOrcidAccount],
    extensions=[
        DatalayerExtension,
    ],
)
