import strawberry
from strawberry.experimental import pydantic
from fakts.base_models import Manifest
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

