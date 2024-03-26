from django.conf import settings
from django.utils.module_loading import import_string
from typing import Protocol
from abc import ABC, abstractclassmethod, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel
from typing import Optional
from fakts.base_models import LinkingContext   



class ServiceDescriptor(BaseModel):
    """ A service descriptor
    
    This is a pydantic model that represents a service. It is used to
    represent a service in the database and in the code.
    """
    identifier: str
    """ The service identifier"""
    key: str
    """ The service key"""
    name: Optional[str]
    """ The service name"""
    logo:  Optional[str]
    """ The service logo"""
    description:  Optional[str] = "No description available"
    """ The service description"""

class InstanceDescriptor(BaseModel):
    """ An instance of a service
    
    This is a pydantic model that represents an instance of a service. It is used to
    represent a service instance in the database and in the code.
    """
    backend_identifier: str 
    """ The backend identifier"""
    instance_identifier: str
    """ The instande_idenrifier (unique for backend)"""
    service_identifier: str
    """ The service identifier"""




class InstanceMap(BaseModel):
    instance_identifier: str
    backend_identifier: str


class CompositionDescriptor(BaseModel):
    """ A composition of services
    
    This is a pydantic model that represents a composition of services. It is used to
    represent a service composition in the database and in the code.
    
    """
    name: Optional[str]
    services: dict[str, InstanceMap]
    """ A map of service identifiers to the correct instance on a backend"""



class Backend(Protocol):

    def __init__(self, config: Dict[str, Any]) -> None: ...

    def render(self, service_identifier, context: LinkingContext) -> Dict[str, Any]: ...

    @classmethod
    def get_name(cls) -> str: ...

    def get_service_descriptors(cls) -> list[ServiceDescriptor]: ...

    def get_instance_descriptors(cls) -> list[InstanceDescriptor]: ...

    def get_composition_descriptors(cls) -> list[CompositionDescriptor]: ...

    @abstractmethod
    def rescan(self) -> None: ...




class BackendBase(ABC):

    @abstractclassmethod
    def get_name(cls) -> str:
        return cls.__name__
    
    def render(cls, service_instance, context: LinkingContext) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_service_descriptors(cls) -> list[ServiceDescriptor]:
        pass
    
    @abstractmethod
    def get_instance_descriptors(cls) -> list[InstanceDescriptor]:
        pass

    @abstractmethod
    def get_composition_descriptors(cls) -> list[CompositionDescriptor]:
        pass
    
    @abstractmethod
    def rescan(self):
        pass




class BackendRegistry:
    backends: dict[str, Backend] = {}

    def __init__(self) -> None:
        if not hasattr(settings, "FAKTS_BACKENDS"):
            self.backend_configs = []
        else:
            self.backend_configs = settings.FAKTS_BACKENDS

        for i in self.backend_configs:
            assert isinstance(i, dict), "Backend configuration must be a dictionary"
            assert "NAME" in i, "Backend configuration must have a NAME"
            self.register(import_string(i["NAME"])(i))

        pass

    def get_backend_identifiers(self):
        names = []

        for i in self.backends.values():
            names.append(i.get_name())

        return names
        

    def register(self, backend):
        self.backends[backend.get_name()] = backend

    def get(self, name):
        return self.backends[name]

    def all(self):
        return self.backends
    
    def get_service_descriptors(self) -> list[ServiceDescriptor]:
        services = []
        for i in self.backends.values():
            services.extend(i.get_service_descriptors())

        return services
    

    def get_composition_descriptors(self) -> list[CompositionDescriptor]:
        compositions = []
        for i in self.backends.values():
            compositions.extend(i.get_composition_descriptors())

        return compositions
    
    def get_instance_descriptors(self) -> list[InstanceDescriptor]:
        instances = []
        for i in self.backends.values():
            instances.extend(i.get_instance_descriptors())

        return instances
    

    def rescan(self):
        for i in self.backends.values():
            print("Rescanning", i.get_name())
            i.rescan()
    


    


