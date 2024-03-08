from fakts.backends.backend_registry import BackendBase, InstanceDescriptor, CompositionDescriptor, InstanceMap, ServiceDescriptor
from fakts.base_models import LinkingContext, LinkingRequest, Manifest, LinkingClient
from typing import Dict, Any
from pathlib import Path
import yaml
from jinja2 import Template, TemplateSyntaxError, TemplateError


class ConfigBackend(BackendBase):
    """
    This class is used to store the configuration of the server. It is
    responsible for reading and writing the configuration to the file system.
    """

    def __init__(self, config: dict) -> None:
        self.config = config
        self.service_dir = Path(self.config.get("SERVICE_DIR", "/workspace/config_backend/services"))
        self.instance_dr = Path(self.config.get("INSTANCE_DIR", "/workspace/config_backend/instances"))
        self.composition_dir = Path(self.config.get("COMPOSITION_DIR", "/workspace/config_backend/compositions"))

        assert self.service_dir.exists(), f"Service directory {self.service_dir} does not exist"
        assert self.composition_dir.exists(), f"Composition directory {self.composition_dir} does not exist"


        self.loaded_services = self._load_services()
        print(self.loaded_services)

        self.loaded_instances = self._load_instances()
        print(self.loaded_instances)

        self.loaded_compositions = self._load_compositions()
        print(self.loaded_compositions)


    def _load_instances(self) -> dict[str, InstanceDescriptor]:
        instances = {}

        for instance_file in self.instance_dr.iterdir():
            if instance_file.is_file():
                instances[instance_file.stem] = self.retrieve_instance(instance_file)

        return instances
    
    def _load_services(self) -> dict[str, ServiceDescriptor]:
        instances = {}

        for service_file in self.service_dir.iterdir():
            if service_file.is_file():
                instances[service_file.stem] = self.retrieve_serve(service_file)

        return instances
    
    def _load_compositions(self) -> dict[str, CompositionDescriptor]:

        compositions = {}

        for composition_file in self.composition_dir.iterdir():
            if composition_file.is_file():
                compositions[composition_file.stem] = self.retrieve_composition(composition_file)

        return compositions
    

    def retrieve_composition(self, composition_file: Path) -> CompositionDescriptor:
        with open(composition_file, "r") as file:
            context = yaml.load(file.read(), Loader=yaml.SafeLoader)

        assert context.get("name"), f"Composition file {composition_file} does not contain a name"
        assert context.get("services"), f"Composition file {composition_file} does not contain any services"

        service_dict = {}

        for service_name, instance_name in context.get("services").items():
            assert self.loaded_instances.get(instance_name), f"Composition file {composition_file} contains an unknown service instance {instance_name}"
            service_dict[service_name] = InstanceMap(instance_identifier=instance_name, backend_identifier=self.get_name())

        return CompositionDescriptor(
            name=context.get("name"),
            services=service_dict
        )
    
    def retrieve_serve(self, service_file: Path) -> ServiceDescriptor:
        with open(service_file, "r") as file:
            context = yaml.load(file.read(), Loader=yaml.SafeLoader)

        assert context.get("key"), f"Service file {service_file} does not contain a key"


        return ServiceDescriptor(
            identifier=service_file.stem,
            key=context.get("key"),
            logo=context.get("logo"),
            description=context.get("description"),
        )



    def retrieve_instance(self, service_file: Path) -> InstanceDescriptor:
        with open(service_file, "r") as file:
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

        assert result.get("__service"), f"Service file {service_file} does not contain an service identifier (\"__service\")"

        return InstanceDescriptor(
            backend_identifier=self.get_name(),
            instance_identifier=service_file.stem,
            service_identifier=result.get("__service"),
        )


    

    def render(self, instance_id: str, linking: LinkingContext) -> Dict[str, Any]:
        with open(self.instance_dr / f"{instance_id}.yaml", "r") as file:
            template = file.read()

        answer = yaml.load(Template(template).render(linking.dict()), Loader=yaml.SafeLoader)
        print(answer)
        return answer




    @classmethod
    def get_name(cls) -> str:
        return cls.__name__
    

    def get_service_descriptors(self) -> list[ServiceDescriptor]:
        return self.loaded_services.values()
    
    def get_instance_descriptors(self) -> list[InstanceDescriptor]:
        return self.loaded_instances.values()
    
    def get_composition_descriptors(self) -> list[CompositionDescriptor]:
        return self.loaded_compositions.values()


        