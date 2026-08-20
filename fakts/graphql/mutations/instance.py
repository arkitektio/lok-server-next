import logging

from kante.types import Info
from django.contrib.auth import get_user_model

from fakts import inputs, models, types
from karakter.authz import get_organization, get_scoped_or_denied

logger = logging.getLogger(__name__)

User = get_user_model()


def update_service_instance(info: Info, input: inputs.UpdateServiceInstanceInput) -> types.ServiceInstance:
    """Update a service instance's access lists.

    These four lists *are* the instance's ACL, so an unscoped lookup here let any
    principal grant themselves access to any tenant's service instance (or deny a
    tenant access to their own). Scoped to the caller's organization.
    """
    instance = get_scoped_or_denied(models.ServiceInstance.objects, info, id=input.id)

    if input.allowed_groups is not None:
        instance.allowed_groups.set(models.Group.objects.filter(id__in=input.allowed_groups))

    if input.allowed_users is not None:
        instance.allowed_users.set(User.objects.filter(id__in=input.allowed_users))

    if input.denied_groups is not None:
        instance.denied_groups.set(models.Group.objects.filter(id__in=input.denied_groups))

    if input.denied_users is not None:
        instance.denied_users.set(User.objects.filter(id__in=input.denied_users))

    return instance


def create_service_instance(info: Info, input: inputs.CreateServiceInstanceInput) -> types.ServiceInstance:
    """
    Create a new service instance.

    Note: the `objects.create` below is broken independently of authorization —
    `identifier` and `service` are not fields on `ServiceInstance` (it has `hub`,
    `release`, `instance_id`, `steward`, `organization`, `template`, all
    non-null), so this raises before creating anything. The guard is still worth
    having: it establishes the caller's organization up front, so if the create
    is ever repaired the instance is owned by a tenant rather than created
    org-less as it was written to be.
    """
    get_organization(info)

    service = get_scoped_or_denied(models.Service.objects, info, id=input.service)

    instance = models.ServiceInstance.objects.create(
        identifier=input.identifier,
        service=service,
    )

    if input.allowed_groups is not None:
        instance.allowed_groups.set(models.Group.objects.filter(id__in=input.allowed_groups))

    if input.allowed_users is not None:
        instance.allowed_users.set(User.objects.filter(id__in=input.allowed_users))

    if input.denied_groups is not None:
        instance.denied_groups.set(models.Group.objects.filter(id__in=input.denied_groups))

    if input.denied_users is not None:
        instance.denied_users.set(User.objects.filter(id__in=input.denied_users))

    return instance
