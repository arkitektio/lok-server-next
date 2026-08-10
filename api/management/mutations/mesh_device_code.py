from kante import Info
import strawberry
from api.management import types
from karakter import models
from fakts import models as fakts_models
from api.management.authz import assert_member
from fakts import logic
import kante


@kante.input
class AcceptMeshDeviceCodeInput:
    """Input for authorizing a machine to join an organization's mesh."""

    device_code: strawberry.ID
    organization: strawberry.ID
    machine_name: str | None = None
    ephemeral: bool = False
    tags: list[str] | None = None


def accept_mesh_device_code(info: Info, input: AcceptMeshDeviceCodeInput) -> types.ManagementMeshDeviceCode:
    """
    Authorize a machine's request to join an organization's mesh.

    Mints a single-use pre-authorized key for the organization's mesh and links it to the
    device code, so the polling machine receives it (along with the coordination URL and
    the authorized machine name). Only members of the organization may authorize.
    """
    user = info.context.request.user
    device_code = fakts_models.MeshDeviceCode.objects.get(id=input.device_code)
    organization = models.Organization.objects.get(id=input.organization)

    assert_member(info, organization)

    key = logic.create_mesh_auth_key(
        user=user,
        organization=organization,
        ephemeral=input.ephemeral,
        tags=input.tags,
    )

    device_code.auth_key = key
    device_code.machine_name = input.machine_name or device_code.requested_machine_name
    device_code.save()

    return device_code


@kante.input
class DeclineMeshDeviceCodeInput:
    """Input for declining a machine's mesh join request."""

    device_code: strawberry.ID


def decline_mesh_device_code(info: Info, input: DeclineMeshDeviceCodeInput) -> types.ManagementMeshDeviceCode:
    """Decline a machine's request to join the mesh, marking the device code as denied."""
    device_code = fakts_models.MeshDeviceCode.objects.get(id=input.device_code)
    device_code.denied = True
    device_code.save()

    return device_code
