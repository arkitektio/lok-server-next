import datetime
import json
from enum import Enum
from typing import Any, Dict, ForwardRef, Literal, Optional, Union

import strawberry
import strawberry_django
from ekke.types import Info
from kammer import enums, filters, models, scalars
from karakter import types
from pydantic import BaseModel, Field
from strawberry import LazyType
from strawberry.experimental import pydantic


@strawberry_django.type(models.Structure)
class Structure:
    id: strawberry.ID
    object: strawberry.ID
    identifier: str


@strawberry_django.type(models.Room)
class Room:
    id: strawberry.ID
    title: str
    description: str

    @strawberry_django.field()
    def messages(self, info) -> list["Message"]:
        return models.Message.objects.filter(agent__room=self).all()


@strawberry_django.type(models.Agent)
class Agent:
    id: strawberry.ID
    room: Room


@strawberry_django.type(models.Message)
class Message:
    id: strawberry.ID
    title: str
    text: str
    agent: Agent
    attached_structures: list[Structure]
