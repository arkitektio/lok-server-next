import strawberry
from strawberry.experimental import pydantic
from fakts.base_models import Manifest, LinkingContext, LinkingRequest
from typing import Optional
from pydantic import BaseModel, Field
import uuid
from fakts import enums




class RequirementModel(BaseModel):
    service: str
    optional: bool = False
    description: Optional[str] = None
    key: str


@pydantic.input(RequirementModel)
class Requirement:
    service: str
    optional: bool = False
    description: Optional[str] = None
    key: str




@pydantic.input(Manifest)
class ManifestInput:
    identifier: str
    version: str
    logo: Optional[str] = None
    scopes: list[str]



class DevelopmentClientInputModel(BaseModel):
    manifest: Manifest 
    composition: str | None = None
    requirements: list[RequirementModel] = Field(default_factory=list)



@pydantic.input(DevelopmentClientInputModel)
class DevelopmentClientInput:
    manifest: ManifestInput
    composition: strawberry.ID | None = None
    requirements: list[Requirement] 


class ScanBackendInputModel(BaseModel):
    backend: str | None



@pydantic.input(ScanBackendInputModel)
class ScanBackendInput:
    backend: str | None = None


@pydantic.input(LinkingRequest)
class LinkingRequestInput:
    host: str
    port: str
    is_secure: bool


@pydantic.input(LinkingContext)
class LinkingContextInput:
    request: LinkingRequestInput
    manifest: ManifestInput



class RenderInputModel(BaseModel):
    client: str
    composition: str | None = None
    request: LinkingRequest | None = None
    manifest: Manifest | None = None

@pydantic.input(RenderInputModel)
class RenderInput:
    client: strawberry.ID
    composition: strawberry.ID | None = None
    request: LinkingRequestInput | None = None
    manifest: ManifestInput | None = None



class KeyValueInputModel(BaseModel):
    key: str
    value: str
    as_type: enums.FaktValueType


class UserDefinedServiceInstanceInputModel(BaseModel):
    identifier: str
    values: list[KeyValueInputModel] = Field(default_factory=list)
    
@pydantic.input(KeyValueInputModel)
class KeyValueInput:
    key: str
    value: str
    as_type: enums.FaktValueType 



@pydantic.input(UserDefinedServiceInstanceInputModel)
class UserDefinedServiceInstanceInput:
    identifier: str
    values: list[KeyValueInput] = strawberry.field(default_factory=list)