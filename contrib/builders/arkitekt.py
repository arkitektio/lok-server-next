from typing import TYPE_CHECKING


if TYPE_CHECKING:

    from fakts.base_models import LinkingContext 
    from contrib.backends.docker_backend import DockerServiceDescriptor, SelfServiceDescriptor


def _create_base_url(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor", inside_port="80/tcp"):
    protocol = "https" if context.secure else "http"
    inside_base_url = f"{protocol}://{descriptor.internal_host}:{inside_port.split('/')[0]}"
    outside_base_url = f"{protocol}://{context.request.host}" + (f"/{descriptor.internal_host}" if descriptor.internal_host != 'lok' else '')
    
    # Depending on how the service is accessed, we need to return the correct base_url
    if context.request.host == self.internal_host:
        base_url = inside_base_url
    else:
        base_url = outside_base_url

    return base_url


def _create_base_wsurl(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor"):
    
    protocol = "wss" if context.secure else "ws"
    inside_base_url = f"{protocol}://{descriptor.internal_host}:80"
    outside_base_url = f"{protocol}://{context.request.host}/{descriptor.internal_host}"
    
    # Depending on how the service is accessed, we need to return the correct base_url
    if context.request.host == self.internal_host:
        base_url = inside_base_url
    else:
        base_url = outside_base_url

    return base_url


def lok(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor"):

    base_url = _create_base_url(self, context, descriptor)



    return { "base_url": base_url + "/o", "userinfo_url": f"{base_url}/o/userinfo", "token_url": f"{base_url}/o/token", "authorization_url": f"{base_url}/o/authorize", "client_id": context.client.client_id, "client_secret": context.client.client_secret, "client_type": context.client.client_type, "grant_type": context.client.authorization_grant_type, "name": context.client.name, "scopes": context.manifest.scopes, "__service": "live.arkitekt.lok"} | generic(self, context, descriptor)


def lok_dep(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor"):

    base_url = _create_base_url(self, context, descriptor)



    return lok(self, context, descriptor) 









def generic(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor"):

    base_url = _create_base_url(self, context, descriptor)
    ws_base_url = _create_base_wsurl(self, context, descriptor)



    return { "endpoint_url": base_url + "/graphql", "healthtz ": f"{base_url}/ht", "ws_endpoint_url": ws_base_url + "/graphql"}



def rekuest(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor"):

    base_url = _create_base_url(self, context, descriptor)
    ws_base_url = _create_base_wsurl(self, context, descriptor)



    return generic(self, context, descriptor) | { "agent": {"endpoint_url": ws_base_url + "/agi"}}


def datalayer(self: "SelfServiceDescriptor", context: "LinkingContext", descriptor: "DockerServiceDescriptor"):

    protocol = "https" if context.secure else "http"
    inside_base_url = f"{protocol}://{descriptor.internal_host}:9000"
    outside_base_url = f"{protocol}://{context.request.host}"

     # Depending on how the service is accessed, we need to return the correct base_url
    if context.request.host == self.internal_host:
        base_url = inside_base_url
    else:
        base_url = outside_base_url



    return { "endpoint_url": base_url}