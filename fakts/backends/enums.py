from fakts.backends.instances import registry
import strawberry
from enum import Enum


BackendType = strawberry.enum(
    Enum("BackendType", {i: i for i in registry.get_backend_identifiers()})
)
