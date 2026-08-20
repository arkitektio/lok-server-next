from kante.types import Info
import strawberry
from django.db.models import Q
from graphql import GraphQLError
from karakter.authz import DENIED, get_user
from pak import types, models, inputs
import logging

logger = logging.getLogger(__name__)


def _writable_stash(info: Info, stash_id: strawberry.ID) -> models.Stash:
    """Fetch a stash the caller may write to: their own, or one shared with them.

    Every resolver in this module already bound `user = info.context.request.user`
    and then never used it, so a bare pk let any principal rename, delete, or add
    items to anyone's stash. `Stash.owner` is the ownership field (note the
    queries in `pak/graphql/queries/stash.py` filter on a `user` field that does
    not exist, and raise `FieldError` — that is a separate pre-existing bug).
    """
    user = get_user(info)
    try:
        return models.Stash.objects.get(
            Q(owner=user) | Q(shared_with=user), id=stash_id
        )
    except models.Stash.DoesNotExist:
        raise GraphQLError(DENIED)


def create_stash(info: Info, input: inputs.CreateStashInput) -> types.Stash:

    user = get_user(info)

    stash = models.Stash.objects.create(
        name=input.name or "Unnamed Stash", owner=user
    )

    return stash


def update_stash(info: Info, input: inputs.UpdateStashInput) -> types.Stash:

    stash = _writable_stash(info, input.stash)
    stash.name = input.name
    stash.description = input.description
    stash.save()

    return stash


def delete_stash(info: Info, input: inputs.DeleteStashInput) -> strawberry.ID:
    # Deleting is owner-only: a stash shared *with* you is not yours to destroy.
    user = get_user(info)
    try:
        stash = models.Stash.objects.get(id=input.stash, owner=user)
    except models.Stash.DoesNotExist:
        raise GraphQLError(DENIED)
    stash.delete()

    return stash


def add_items_to_stash(
    info: Info, input: inputs.AddItemToStashInput
) -> list[types.StashItem]:

    user = get_user(info)

    stash = _writable_stash(info, input.stash)
    created = []
    for item_input in input.items:
        item, _ = models.StashItem.objects.update_or_create(
            identifier=item_input.identifier,
            object=item_input.object,
            stash=stash,
            defaults=dict(added_by=user),
        )
        created.append(item)

    return created


def delete_stash_items(
    info: Info, input: inputs.DeleteStashItems
) -> list[strawberry.ID]:

    user = get_user(info)
    deleted = []
    for item_input in input.items:
        # Scope by the *parent stash's* access, not by who added the item, so a
        # stash owner can still clear items someone they shared with added.
        try:
            item = models.StashItem.objects.get(
                Q(stash__owner=user) | Q(stash__shared_with=user), id=item_input
            )
        except models.StashItem.DoesNotExist:
            raise GraphQLError(DENIED)
        item.delete()
        deleted.append(item_input)

    return deleted
