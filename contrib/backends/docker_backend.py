from fakts.backends.backend_registry import BackendBase, InstanceDescriptor, ServiceDescriptor
from typing import Dict, Any, Callable
from fakts.base_models import LinkingContext
from pydantic import BaseModel
from pathlib import Path
import docker 
import docker
import re
import socket
from django.conf import settings
from django.utils.module_loading import import_string
from pydantic import validator
import logging


logger = logging.getLogger(__name__)


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
    for key, port in ports.items():
        first_port = port[0]
        yield key, first_port["HostPort"]


def get_docker_service_from_container(container):
    return container.labels.get("com.docker.compose.service")
    

class DockerServiceDescriptor(BaseModel):
    internal_host: str
    ''' The internal host of the service'''
    port_map: Dict[str, str]
    ''' The port mapping from the internal port to the external port'''
    config: Dict[str, Any]
    ''' The configuration of the service'''
    labels: Dict[str, str]
    ''' The builder of the service'''
    builder: str




class SelfServiceDescriptor(BaseModel):
    internal_host: str
    ''' The internal host of the service'''
    port_map: Dict[str, str]
    ''' The port mapping from the internal port to the external port'''
    config: Dict[str, Any]
    ''' The configuration of the service'''
    labels: Dict[str, str]
    ''' The builder of the service'''




class DockerConfig(BaseModel):
    NAME: str
    BUILDERS: list[str]
    DEFAULT_BUILDER: str | None = None
    BUILDERS_PATH = "contrib.builders"




class DockerBackend(BackendBase):
    """
    This class is used to store the configuration of the server. It is
    responsible for reading and writing the configuration to the file system.
    """
    loaded_services: Dict[str, DockerServiceDescriptor] = {}
    loaded_docker_service_descriptors: Dict[str, DockerServiceDescriptor] = {}
    loaded_builders: Dict[str, Callable]= {}


    def __init__(self, config_values):
        self.config = DockerConfig(**config_values)



        self.client = docker.from_env()

        self.loaded_services = {}
        self.loaded_instances = {}
        self.loaded_contexts = {}
        self.self_service_descriptor = None


        for i in self.config.BUILDERS:
            if i.startswith("external://"):
                self.register(i, import_string(i[len("external://"):]))
            else:
                self.register(i, import_string(self.config.BUILDERS_PATH + "."+i))


        self.default_builder = self.config.DEFAULT_BUILDER or self.config.BUILDERS[0]


        self.self_container = get_my_container(self.client)

        self.self_labels = self.self_container.labels

        self.self_service_descriptor = SelfServiceDescriptor(
            internal_host=self.self_container.attrs["NetworkSettings"]["IPAddress"],
            port_map=dict(build_ports_dict(self.self_container)),
            config=dict(build_config_dict(self.self_labels)),
            labels=self.self_labels,
        )

        self.self_project_name = get_project_name(self.self_container)

        logger.info(f"Self container: {self.self_container}")
        logger.info(f"Self project name: {self.self_project_name}")
        logger.info(f"Self labels: {self.self_labels}")


    def register(self, key, builder):
        self.loaded_builders[key] = builder


    def _is_fakts_enabled(self, container):
        """ In order to be a Fakts container, the container must have a label that starts with fakts.composition and ends with key
        
        e.g. 

        fakts.composition.default.key: fluss

        
        """

        for label, value in container.labels.items():
            if label == "fakts.service":
                return True
                
        return False
            
        



    def rescan(self):
        
        loading_services = {}
        loading_service_descriptors = {}
        loading_instances = {}


        sibling_containers = retrieve_sibling_containers(self.client, self.self_project_name)


        for container in sibling_containers:

            labels = container.labels

            if self._is_fakts_enabled(container):

                # This is a Fakts enabled container
                
                service_identifier = labels["fakts.service"]
                instance_identifier = get_docker_service_from_container(container)


                logger.info(f"Found Fakts enabled service {instance_identifier}")




                if service_identifier in loading_services:
                    # Service already loaded just updating the labels if they are
                    # not already set
                    service_descriptor = loading_services[service_identifier]
                    if service_descriptor.logo is None:
                        service_descriptor.logo = labels.get("fakts.service.logo")
                    if service_descriptor.description is None:
                        service_descriptor.description = labels.get("fakts.service.description")
                    if service_descriptor.validator is None:
                        service_descriptor.validator = labels.get("fakts.service.validator")
                else:
                    
                    service_descriptor = ServiceDescriptor(
                        identifier=service_identifier,
                        name=labels.get("fakts.service.name"),
                        logo=labels.get("fakts.service.logo"),
                        description=labels.get("fakts.service.description"),
                        validator=labels.get("fakts.service.validator"),
                    )


                    loading_services[service_descriptor.identifier] = service_descriptor



                # Register the instance
                instance_descriptor = InstanceDescriptor(
                    backend_identifier=self.get_name(),
                    instance_identifier=instance_identifier,
                    service_identifier=service_descriptor.identifier,
                )


                # Lets check if the builder is valid
                builder = labels.get("fakts.builder", self.default_builder)
                assert builder in self.loaded_builders, f"Builder {builder} not found. Cannot register instance"

                # Overwriting the instance if it already exists is okay, because
                # the configuration is done on the service level, however some
                loading_instances[instance_descriptor.instance_identifier] = instance_descriptor


                port_map = dict(build_ports_dict(container))
                config = dict(build_config_dict(labels))
                print(port_map)
                print(config)
                
                # Containers might have different configurations for different instances
                # we update the configuration if it is not already set
                if instance_descriptor.instance_identifier in loading_service_descriptors:
                    # Service already loaded just updating the labels if they are
                    # not already set
                    instance_descriptor = loading_service_descriptors[instance_descriptor.instance_identifier]
                    instance_descriptor.port_map.update(port_map)
                    instance_descriptor.labels.update(labels)
                    instance_descriptor.config.update(config)
                else:
                    docker_service_descriptor = DockerServiceDescriptor(
                            internal_host=instance_identifier,
                            port_map=port_map,
                            config=config,
                            labels=labels,
                            builder=builder
                    )



                    loading_service_descriptors[instance_descriptor.instance_identifier] = docker_service_descriptor





                
              

        

        self.loaded_services = loading_services
        self.loaded_instances = loading_instances
        self.loaded_docker_service_descriptors = loading_service_descriptors


    @classmethod
    def get_name(cls) -> str:
        return cls.__name__
    
    
    def render(self, service_instance: str, context: LinkingContext) -> Dict[str, Any]:
        
        # We need to check if the service instance is in the loaded services (maybe we restarted the server)
        if service_instance not in self.loaded_docker_service_descriptors:
            self.rescan()


        assert service_instance in self.loaded_docker_service_descriptors, f"Service instance {service_instance} (after retry) not found"
        service = self.loaded_docker_service_descriptors[service_instance]


        assert service.builder in self.loaded_builders, f"Builder {service.builder} not found in loaded builders"
        builder = self.loaded_builders[service.builder]

        return builder(self.self_service_descriptor, context, service)


    def get_service_descriptors(self) -> list[ServiceDescriptor]:
        return self.loaded_services.values()
    
    def get_instance_descriptors(self) -> list[InstanceDescriptor]:
        return self.loaded_instances.values()
    