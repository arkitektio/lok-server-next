from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Literal


class LayerModel(BaseModel):
    """Model representing a layer in the system."""

    identifier: str
    name: Optional[str] = None
    kind: Literal["loopback", "lan", "tailscale", "vpn", "public", "docker", "kubernetes", "tor", "zerotier", "manual", "proxy", "web"]
    logo: Optional[str] = None
    description: Optional[str] = "No description available"
    get_probe: Optional[str] = None


class AliasModel(BaseModel):
    """Model representing an alias for a service instance."""

    layer: str
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    path: Optional[str] = None
    kind: Optional[Literal["relative", "absolute"]] = "relative"
    challenge: str = Field(default="ht", description="A challenge url to verify the alias on the client. If it returns a 200 OK, the alias is valid. It can additionally return a JSON object with a `challenge` key that contains the challenge to be solved by the client.")


class ServiceInstanceModel(BaseModel):
    """Model representing a service instance."""

    service: str
    identifier: str
    aliases: List[AliasModel]


class YamlConfigModel(BaseModel):
    """Model representing the YAML configuration."""

    layers: List[LayerModel]
    instances: List[ServiceInstanceModel]

    @model_validator(mode="after")
    def validate_aliases_layers(self) -> "YamlConfigModel":
        """Validate that all alias layers reference existing layers."""
        layer_ids = {layer.identifier for layer in self.layers}

        for instance in self.instances:
            for alias in instance.aliases:
                if alias.layer not in layer_ids:
                    raise ValueError(f"Alias layer '{alias.layer}' in instance '{instance.identifier}' does not exist in defined layers. Allowed Layers: {', '.join(layer_ids)}")

        return self
