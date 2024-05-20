from ekke.types import Info
import strawberry_django
import strawberry
from pak import types, models, inputs, enums, scalars
import hashlib
import json
import logging
from karakter.hashers import hash_graph
import namegenerator

logger = logging.getLogger(__name__)




def create_stash(info: Info, input: inputs.CreateStashInput) -> types.Stash:

    user = info.context.request.user

    stash = models.Stash.objects.create(
        name=input.name or namegenerator.gen(),
        owner=user
    )

    return stash


def update_stash(info: Info, input: inputs.UpdateStashInput) -> types.Stash:
    
    user = info.context.request.user

    stash = models.Stash.objects.get(id=input.stash)
    stash.name = input.name
    stash.description = input.description
    stash.save()

    return stash


def delete_stash(info: Info, input: inputs.DeleteStashInput) -> strawberry.ID:
        
    user = info.context.request.user

    stash = models.Stash.objects.get(id=input.stash)
    stash.delete()

    return stash

def add_items_to_stash(info: Info, input: inputs.AddItemToStashInput) -> list[types.StashItem]:
    
    user = info.context.request.user

    stash = models.Stash.objects.get(id=input.stash)
    created = []
    for item_input in input.items:
        item, _ = models.StashItem.objects.update_or_create(
            identifier=item_input.identifier,
            object=item_input.object,
            stash=stash,
            defaults=dict(added_by=user)
        )
        created.append(item)

    return created

def delete_stash_items(info: Info, input: inputs.DeleteStashItems) -> list[strawberry.ID]:
    
    user = info.context.request.user
    deleted = []
    for item_input in input.items:
        item = models.StashItem.objects.get(id=item_input)
        item.delete()
        deleted.append(item_input)


    return deleted





