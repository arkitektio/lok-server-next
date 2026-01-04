from kante import Info
import strawberry
from api.management import types
from karakter import models
from django.utils import timezone
from datetime import timedelta
import kante
from fakts import models as fakts_models


@kante.input
class CreateAliasInput:
    """Input for creating a single-use magic invite link for an organization"""

    service_instance: strawberry.ID  # Service Instance ID to create the alias for
    port: int
    host: str
    kind: str
    path: str | None = None


def create_alias(info: Info, input: CreateAliasInput) -> types.ManagementInstanceAlias:
    """ """

    user = info.context.request.user
    service_instance = fakts_models.ServiceInstance.objects.get(id=input.service_instance)

    alias = fakts_models.InstanceAlias.objects.create(
        service_instance=service_instance,
        port=input.port,
        host=input.host,
        kind=input.kind,
        path=input.path,
        created_by=user,
    )

    return alias


@kante.input
class UpdateAliasInput:
    """Input for creating a single-use magic invite link for an organization"""

    id: strawberry.ID
    port: int
    host: str
    kind: str
    path: str | None = None


def update_alias(info: Info, input: UpdateAliasInput) -> types.ManagementInstanceAlias:
    """ """

    user = info.context.request.user

    alias = fakts_models.InstanceAlias.objects.get(id=input.id)
    alias.port = input.port
    alias.host = input.host
    alias.kind = input.kind
    alias.path = input.path
    alias.save()

    return alias


@kante.input
class DeleteAliasInput:
    """Input for accepting an organization invite"""

    id: strawberry.ID


def delete_alias(info: Info, input: DeleteAliasInput) -> strawberry.ID:
    """
    Accept an invite to join an organization.

    Validates the invite token and adds the user to the organization.
    """
    try:
        alias = fakts_models.InstanceAlias.objects.get(id=input.id)
    except fakts_models.InstanceAlias.DoesNotExist:
        raise Exception("Invalid alias ID")

    alias.delete()

    return input.id
