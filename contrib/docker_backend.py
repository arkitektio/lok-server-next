from fakts.backends.backend_registry import BackendBase, InstanceDescriptor, CompositionDescriptor, ServiceDescriptor, InstanceMap
from typing import Dict, Any
from fakts.base_models import LinkingContext
from pydantic import BaseModel
from pathlib import Path
import docker 
import docker
import re
import socket
import yaml
from jinja2 import Template, TemplateSyntaxError, TemplateError


def get_my_container(client: docker.DockerClient):

    container_id = socket.gethostname()

    try: 
        return client.containers.get(container_id)
    except docker.errors.NotFound:

        potential_container_id = None

        try:
            with open("/proc/self/cgroup", "r") as file:
                for line in file:
                    match = re.search(r'/docker/([a-f0-9]{64})$', line)
                    if match:
                        potential_container_id = match.group(1)
                        break

        except FileNotFoundError:
            raise Exception("Could not find container id")
        
        if potential_container_id:
            return client.containers.get(potential_container_id)
        else:
            raise Exception("Could not find container id")



def get_project_name(container):
    return container.labels.get("com.docker.compose.project")


def retrieve_sibling_containers(client: docker.DockerClient, project_name: str):
    # Filter containers by Docker Compose project label
    filters = {"label": f"com.docker.compose.project={project_name}"}
    containers = client.containers.list(all=True, filters=filters)
    return containers


def build_config_dict(labels):
    for key, value in labels.items():
        if key.startswith("fakts.instance.config."):
            config_key = key[len("fakts.instance.config."):]
            for level in reversed(config_key.split(".")):
                value = {level: value}
                latest_level = level

            yield config_key, value[latest_level]


def build_ports_dict(container):
    ports = container.attrs["NetworkSettings"]["Ports"]
    print(ports)
    for key, port in ports.items():
        first_port = port[0]
        yield key, first_port["HostPort"]

    

class DockerServiceDescriptor(BaseModel):
    internal_host: str
    ''' The internal host of the service'''
    port_map: Dict[str, str]
    ''' The port mapping from the internal port to the external port'''
    config: Dict[str, Any]
    ''' The configuration of the service'''
    labels: Dict[str, str]
    ''' The labels of the service'''
    template: str




class SelfServiceDescriptor(BaseModel):
    internal_host: str
    internal_port: int = 80
    external_port: int



class DockerContext(BaseModel):
    self: SelfServiceDescriptor






class DockerBackend(BackendBase):
    """
    This class is used to store the configuration of the server. It is
    responsible for reading and writing the configuration to the file system.
    """
    loaded_services: Dict[str, DockerServiceDescriptor] = {}
    loaded_docker_service_descriptors: Dict[str, DockerServiceDescriptor] = {}



    def __init__(self, config_file):
        self.config_file = config_file
        self.client = docker.from_env()

        self.template_dir = Path(self.config_file.get("TEMPLATE_DIR", "/workspace/docker_backend/templates"))

        assert self.template_dir.exists(), f"Template directory {self.template_dir} does not exist"

        self.loaded_services = {}
        self.loaded_compositions = {}
        self.loaded_instances = {}
        self.loaded_contexts = {}

        self.default_composition = "default"
        self.default_template = "live.arkitekt.generic"






    def rescan(self):
        container = get_my_container(self.client)

        project_name = get_project_name(container)
        print(project_name)
        print(container)


        loading_services = {}
        loading_compositions = {}
        loading_service_descriptors = {}
        loading_instances = {}


        sibling_containers = retrieve_sibling_containers(self.client, project_name)


        for container in sibling_containers:

            labels = container.labels

            if "fakts.service.key" in labels:
                service_key = labels["fakts.service.key"]
                service_identifier = labels.get("fakts.service.identifier", service_key)
                instance_identifier = container.id
                composition_identifier = labels.get("fakts.service.composition", self.default_composition)


                if service_key in loading_services:
                    raise Exception(f"Service with key {service_key} already exists")
                
                service_descriptor = ServiceDescriptor(
                    key=service_key,
                    identifier=service_identifier,
                    name=labels.get("fakts.service.name"),
                    logo=labels.get("fakts.service.logo"),
                    description=labels.get("fakts.service.description"),
                )


                loading_services[service_descriptor.identifier] = service_descriptor


                instance_descriptor = InstanceDescriptor(
                    backend_identifier=self.get_name(),
                    instance_identifier=instance_identifier,
                    service_identifier=service_descriptor.identifier,
                )


                loading_instances[instance_descriptor.instance_identifier] = instance_descriptor


                docker_service_descriptor = DockerServiceDescriptor(
                    internal_host=container.attrs["NetworkSettings"]["IPAddress"],
                    port_map=dict(build_ports_dict(container)),
                    config=dict(build_config_dict(labels)),
                    labels=labels,
                    template=labels.get("fakts.service.template", self.default_template)
                )

                loading_service_descriptors[instance_descriptor.instance_identifier] = docker_service_descriptor

                potential_template_name = f"{docker_service_descriptor.template}.yaml"

                if not (self.template_dir / potential_template_name).exists():
                    raise Exception(f"Template {potential_template_name} does not exist")



                if composition_identifier not in loading_compositions:
                    loading_compositions[composition_identifier] = CompositionDescriptor(
                        key=composition_identifier,
                        name=labels.get("fakts.composition.name", composition_identifier),
                        services={ service_key: InstanceMap(instance_identifier=instance_identifier, backend_identifier=self.get_name())},
                    )
                else:
                    loading_compositions[composition_identifier].services[service_key] = InstanceMap(instance_identifier=instance_identifier, backend_identifier=self.get_name())


        self.loaded_services = loading_services
        self.loaded_compositions = loading_compositions
        self.loaded_instances = loading_instances
        self.loaded_docker_service_descriptors = loading_service_descriptors

        print(self.loaded_services)



    @classmethod
    def get_name(cls) -> str:
        return cls.__name__
    
    def render(self, service_instance: str, context: LinkingContext) -> Dict[str, Any]:

        assert service_instance in self.loaded_docker_service_descriptors, f"Service instance {service_instance} not found"
        service = self.loaded_docker_service_descriptors[service_instance]



        with open(self.template_dir / f"{service.template}.yaml", "r") as file:
            template = file.read()


        context = {**context.dict(), **{"service": service.dict()}}
        answer = yaml.load(Template(template).render(context), Loader=yaml.SafeLoader)
        print(answer)
        return answer








        pass

    def get_service_descriptors(self) -> list[ServiceDescriptor]:
        return self.loaded_services.values()
    
    def get_instance_descriptors(self) -> list[InstanceDescriptor]:
        return self.loaded_instances.values()
    
    def get_composition_descriptors(self) -> list[CompositionDescriptor]:
        return self.loaded_compositions.values()