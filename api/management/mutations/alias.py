from kante import Info
import strawberry
from api.management import types
import kante
from fakts import models as fakts_models


@kante.input
class CreateAliasInput:
    """Input for creating an alias for a service instance."""

    instance: strawberry.ID  # Service Instance ID to create the alias for
    port: int
    host: str
    kind: str
    path: str | None = None
    public: bool = False


def create_alias(info: Info, input: CreateAliasInput) -> types.ManagementInstanceAlias:
    """Create an alias for a service instance."""

    instance = fakts_models.ServiceInstance.objects.get(id=input.instance)

    alias = fakts_models.InstanceAlias.objects.create(
        instance=instance,
        port=input.port,
        host=input.host,
        kind=input.kind,
        path=input.path,
        public=input.public,
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
    public: bool | None = None


def update_alias(info: Info, input: UpdateAliasInput) -> types.ManagementInstanceAlias:
    """Update an existing alias for a service instance."""

    alias = fakts_models.InstanceAlias.objects.get(id=input.id)
    alias.port = input.port
    alias.host = input.host
    alias.kind = input.kind
    alias.path = input.path
    if input.public is not None:
        alias.public = input.public
    alias.save()

    return alias


@kante.input
class DeleteAliasInput:
    """Input for deleting an alias."""

    id: strawberry.ID


def delete_alias(info: Info, input: DeleteAliasInput) -> strawberry.ID:
    """Delete an alias for a service instance, returning the deleted alias id."""
    try:
        alias = fakts_models.InstanceAlias.objects.get(id=input.id)
    except fakts_models.InstanceAlias.DoesNotExist:
        raise Exception("Invalid alias ID")

    alias.delete()

    return input.id
