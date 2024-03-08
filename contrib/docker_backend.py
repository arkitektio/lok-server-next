from fakts.backends.backend_registry import BackendBase, InstanceDescriptor, CompositionDescriptor, ServiceDescriptor
from typing import Dict, Any
from fakts.base_models import LinkingContext


class DockerBackend(BackendBase):
    """
    This class is used to store the configuration of the server. It is
    responsible for reading and writing the configuration to the file system.
    """

    def __init__(self, config_file):
        self.config_file = config_file

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__
    
    def render(cls, service_instance: str, context: LinkingContext) -> Dict[str, Any]:
        pass

    def get_instance_descriptors(cls) -> list[InstanceDescriptor]:
        return []
    
    def get_composition_descriptors(self) -> list[CompositionDescriptor]:
        return []
    
    def get_service_descriptors(self) -> list[ServiceDescriptor]:
        return []