from kante import Info
import strawberry_django
import strawberry
from karakter import types, models, inputs, enums, scalars
import hashlib
import json
import logging
from karakter.hashers import hash_graph
import namegenerator
import kante


logger = logging.getLogger(__name__)


@strawberry.input
class CreateUserInput:
    name: str


def create_user(info: Info, input: CreateUserInput) -> types.User:
    trace = models.User(name=input.user)
    return trace


@kante.input
class AddUserToOrganizationInput:
    user: strawberry.ID
    organization: strawberry.ID
    roles: list[str]


def add_user_to_organization(info: Info, input: AddUserToOrganizationInput) -> types.Membership:
    org = input.organization
    user = input.user
    
    
    x, _ = models.Membership.objects.get_or_create(
        user_id=user,
        organization_id=org,
    )
    
    x.roles.clear()
    for role in input.roles:
        
        role =models.Role.objects.get(identifier=role, organization_id=org)
        
        x.roles.add(role)
    
    
    return x

