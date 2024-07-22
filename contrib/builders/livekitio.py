from typing import TYPE_CHECKING


if TYPE_CHECKING:

    from fakts.base_models import LinkingContext 
    from contrib.backends.docker_backend import DockerServiceDescriptor, SelfServiceDescriptor


def _create_base_url(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor", inside_port="80/tcp"):

    protocol = "http" #TODO: Until livekit supports custom certificates
    inside_base_url = f"{protocol}://{descriptor.internal_host}:{inside_port.split('/')[0]}"
    outside_base_url = f"{protocol}://{context.request.host}:7880"
    
    # Depending on how the service is accessed, we need to return the correct base_url
    if context.request.host == self.internal_host:
        base_url = inside_base_url
    else:
        base_url = outside_base_url

    return base_url



def livekit(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor"):

    base_url = _create_base_url(self, context, descriptor)



    return { "endpoint_url": base_url }


