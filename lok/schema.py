from ekke.types import Info
from typing import AsyncGenerator
from typing import Any, Type
import strawberry_django
import strawberry
from ekke.directives import upper, replace, relation
from strawberry_django.optimizer import DjangoOptimizerExtension
from karakter.graphql import mutations as karakter_mutations
from karakter.graphql import queries as karakter_queries
from karakter.graphql import subscriptions as karakter_subscriptions
from fakts.graphql import mutations as fakts_mutations
from fakts.graphql import queries as fakts_queries
from fakts.graphql import subscriptions as fakts_subscriptions
from fakts import types as fakts_types
from karakter import types as karakter_types
from komment import types as komment_types
from komment.graphql import mutations as komment_mutations
from komment.graphql import queries as komment_queries
from komment.graphql import subscriptions as komment_subscriptions
from pak.graphql import mutations as pak_mutations
from pak import types as pak_types
from pak.graphql import queries as pak_queries
from pak.graphql import subscriptions as pak_subscriptions

@strawberry.type
class Query:
    stashes: list[pak_types.Stash] = strawberry_django.field()
    stash_items: list[pak_types.StashItem] = strawberry_django.field()
    my_stashes = strawberry_django.field(resolver=pak_queries.my_stashes)

    apps: list[fakts_types.App] = strawberry_django.field()
    releases: list[fakts_types.Release] = strawberry_django.field()
    clients: list[fakts_types.Client] = strawberry_django.field()
    compositions: list[fakts_types.Composition] = strawberry_django.field()
    users: list[karakter_types.User] = strawberry_django.field()
    groups: list[karakter_types.Group] = strawberry_django.field()
    comments: list[komment_types.Comment] = strawberry_django.field()

    user = strawberry_django.field(resolver=karakter_queries.user)
    me = strawberry_django.field(resolver=karakter_queries.me)
    group = strawberry_django.field(resolver=karakter_queries.group)
    mygroups = strawberry_django.field(resolver=karakter_queries.mygroups)


    app = strawberry_django.field(resolver=fakts_queries.app)
    release = strawberry_django.field(resolver=fakts_queries.release)
    client = strawberry_django.field(resolver=fakts_queries.client)
    my_managed_clients = strawberry_django.field(resolver=fakts_queries.my_managed_clients)
    scopes = strawberry_django.field(resolver=fakts_queries.scopes)


    comment = strawberry_django.field(resolver=komment_queries.comment)
    comments_for = strawberry_django.field(resolver=komment_queries.comments_for)
    my_mentions = strawberry_django.field(resolver=komment_queries.my_mentions)
    redeem_tokens: list[fakts_types.RedeemToken] = strawberry_django.field()

    stash: pak_types.Stash = strawberry_django.field(resolver=pak_queries.stash)
    stash_item: pak_types.StashItem = strawberry_django.field(resolver=pak_queries.stash_item)

    @strawberry_django.field()
    def hallo(self, info: Info) -> str:
        print("hallo")
        return "hallo"


@strawberry.type
class Mutation:
    create_user = strawberry_django.mutation(
        resolver=karakter_mutations.create_user,
    )
    create_comment = strawberry_django.mutation(
        resolver=komment_mutations.create_comment,
    )
    reply_to = strawberry_django.mutation(
        resolver=komment_mutations.reply_to,
    )
    resolve_comment = strawberry_django.mutation(
        resolver=komment_mutations.resolve_comment,
    )
    create_developmental_client = strawberry_django.mutation(
        resolver=fakts_mutations.create_developmental_client,
    )
    scan = strawberry_django.mutation(
        resolver=fakts_mutations.scan_backend,
    )
    render = strawberry_django.mutation(
        resolver=fakts_mutations.render_composition,
    )

    create_stash = strawberry_django.mutation(
        resolver=pak_mutations.create_stash,
        description="Create a new stash",
    )
    update_stash = strawberry_django.mutation(
        resolver=pak_mutations.update_stash,
        description="Update a stash"
    )
    add_items_to_stash = strawberry_django.mutation(
        resolver=pak_mutations.add_items_to_stash,
        description="Add items to a stash"
    )
    delete_stash_items = strawberry_django.mutation(
        resolver=pak_mutations.delete_stash_items,
        description="Delete items from a stash"
    )
    delete_stash = strawberry_django.mutation(
        resolver=pak_mutations.delete_stash,
    )


@strawberry.type
class Subscription:
    communications = strawberry.subscription(resolver=karakter_subscriptions.communications)
    mentions = strawberry.subscription(resolver=komment_subscriptions.mentions)


schema = strawberry.Schema(
    query=Query,
    subscription=Subscription,
    mutation=Mutation,
    directives=[upper, replace, relation],
    extensions=[
        DjangoOptimizerExtension,
    ],
    types=[
        komment_types.Descendant,
        komment_types.MentionDescendant,
        komment_types.ParagraphDescendant,
        komment_types.LeafDescendant,
        karakter_types.GenericAccount,
        karakter_types.OrcidAccount,
    ]  # We really need to register
    # all the types here, otherwise the schema will not be able to resolve them
    # and will throw a cryptic error
)
