import strawberry
from strawberry.experimental import pydantic
from fakts.base_models import Manifest, LinkingContext, LinkingRequest
from typing import Optional
from pydantic import BaseModel, Field
import uuid

@pydantic.input(Manifest)
class ManifestInput:
    identifier: str
    version: str
    logo: Optional[str] = None
    scopes: list[str]



class DevelopmentClientInputModel(BaseModel):
    manifest: Manifest 
    composition: str | None = None



@pydantic.input(DevelopmentClientInputModel)
class DevelopmentClientInput:
    manifest: ManifestInput
    composition: strawberry.ID | None = None


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
    composition: str
    request: LinkingRequest | None = None
    manifest: Manifest | None = None

@pydantic.input(RenderInputModel)
class RenderInput:
    composition: strawberry.ID
    client: strawberry.ID
    request: LinkingRequestInput | None = None
    manifest: ManifestInput | None = None