import logging
from pathlib import Path
from typing import Any, Dict

import yaml
from jinja2 import Template, TemplateError, TemplateSyntaxError

from fakts.backends.backend_registry import (
    BackendBase,
    InstanceDescriptor,
    ServiceDescriptor,
)
from fakts.base_models import LinkingClient, LinkingContext, LinkingRequest, Manifest
from pydantic import BaseModel
logger = logging.getLogger(__name__)


class ConfigBackendConfig(BaseModel):
    INSTANCE_DIR: str = "/workspace/contrib/config_instances"

class ConfigBackend(BackendBase):
    """
    This class is used to store the configuration of the server. It is
    responsible for reading and writing the configuration to the file system.
    """

    def __init__(self, config: dict) -> None:
        self.config = ConfigBackendConfig(**config)
        self.instance_dir = Path(self.config.INSTANCE_DIR)

        assert self.instance_dir.exists(), f"Instance directory {self.instance_dir} does not exist"


        self.loaded_services = {}
        self.loaded_instances = {}

        self.rescan()


    def rescan(self) -> None:
        loading_instances = {}
        loading_services = {}

        for instance_file in self.instance_dir.iterdir():
            if instance_file.is_file():
                try:
                    with open(instance_file, "r") as file:
                        template = file.read()


                    fake_context = LinkingContext(
                        request=LinkingRequest(
                            host="example.com",
                            port="443",
                            is_secure=True,
                        ),
                        manifest=Manifest(
                            identifier="com.example.app",
                            version="1.0",
                            scopes=["scope1", "scope2"],
                            redirect_uris=["https://example.com"],
                        ),
                        client=LinkingClient(
                            client_id="@client_id",
                            client_secret="@client_secret",
                            client_type="@client_type",
                            authorization_grant_type="authorization_grant_type",
                            name="@name",
                        ),
                    )


                    result = yaml.load(Template(template).render(fake_context), Loader=yaml.SafeLoader)

                    service_config = result.get("__service")

                    assert service_config, f"Service file {instance_file} does not contain an service identifier (\"__service\")"

                    service_descriptor = ServiceDescriptor(**service_config)

                    loading_instances[instance_file.stem] = InstanceDescriptor(
                        backend_identifier=self.get_name(),
                        instance_identifier=instance_file.stem,
                        service_identifier=service_descriptor.identifier,
                    )

                    loading_services[service_descriptor.identifier] = service_descriptor


                    logger.info(f"Loaded instance {instance_file.stem} for service {service_descriptor.identifier}")


                except Exception as e:
                    raise ValueError(f"Error loading instance {instance_file}: {e}") from e

        self.loaded_instances = loading_instances
        self.loaded_services = loading_services

    


    

    def render(self, instance_id: str, linking: LinkingContext) -> Dict[str, Any]:
        with open(self.instance_dir / f"{instance_id}.yaml", "r") as file:
            template = file.read()

        answer = yaml.load(Template(template).render(linking.dict()), Loader=yaml.SafeLoader)
        return answer




    @classmethod
    def get_name(cls) -> str:
        return cls.__name__
    

    def get_service_descriptors(self) -> list[ServiceDescriptor]:
        return self.loaded_services.values()
    
    def get_instance_descriptors(self) -> list[InstanceDescriptor]:
        return self.loaded_instances.values()
    

        