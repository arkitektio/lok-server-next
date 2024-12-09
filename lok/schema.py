from typing import Any, AsyncGenerator, Type

import strawberry
import strawberry_django
from ekke.directives import relation, replace, upper
from ekke.types import Info
from fakts import types as fakts_types
from fakts.graphql import mutations as fakts_mutations
from fakts.graphql import queries as fakts_queries
from fakts.graphql import subscriptions as fakts_subscriptions
from fakts import models as fakts_models
from kammer import types as kammer_types
from kammer.graphql import mutations as kammer_mutations
from kammer.graphql import queries as kammer_queries
from kammer.graphql import subscriptions as kammer_subscriptions
from karakter import types as karakter_types
from karakter.graphql import mutations as karakter_mutations
from karakter.graphql import queries as karakter_queries
from karakter.graphql import subscriptions as karakter_subscriptions
from komment import types as komment_types
from komment.graphql import mutations as komment_mutations
from komment.graphql import queries as komment_queries
from komment.graphql import subscriptions as komment_subscriptions
from pak import types as pak_types
from pak.graphql import mutations as pak_mutations
from pak.graphql import queries as pak_queries
from pak.graphql import subscriptions as pak_subscriptions
from strawberry_django.optimizer import DjangoOptimizerExtension


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
    rooms: list[kammer_types.Room] = strawberry_django.field()
    services: list[fakts_types.Service] = strawberry_django.field()
    service_instances: list[fakts_types.ServiceInstance] = strawberry_django.field()

    user = strawberry_django.field(resolver=karakter_queries.user)
    me = strawberry_django.field(resolver=karakter_queries.me)
    group = strawberry_django.field(resolver=karakter_queries.group)
    mygroups = strawberry_django.field(resolver=karakter_queries.mygroups)

    room = strawberry_django.field(resolver=kammer_queries.room)
    stream = strawberry_django.field(resolver=kammer_queries.stream)

    app = strawberry_django.field(resolver=fakts_queries.app)
    release = strawberry_django.field(resolver=fakts_queries.release)
    client = strawberry_django.field(resolver=fakts_queries.client)
    my_managed_clients = strawberry_django.field(
        resolver=fakts_queries.my_managed_clients
    )
    scopes = strawberry_django.field(resolver=fakts_queries.scopes)

    comment = strawberry_django.field(resolver=komment_queries.comment)
    comments_for = strawberry_django.field(resolver=komment_queries.comments_for)
    my_mentions = strawberry_django.field(resolver=komment_queries.my_mentions)
    redeem_tokens: list[fakts_types.RedeemToken] = strawberry_django.field()

    stash: pak_types.Stash = strawberry_django.field(resolver=pak_queries.stash)
    stash_item: pak_types.StashItem = strawberry_django.field(
        resolver=pak_queries.stash_item
    )
    my_active_messages = strawberry_django.field(
        resolver=karakter_queries.my_active_messages
    )
    message = strawberry_django.field(resolver=karakter_queries.message)


    @strawberry_django.field()
    def hallo(self, info: Info) -> str:
        print("hallosss")
        return "hallo"
    
    @strawberry_django.field()
    def service(self, info: Info, id: strawberry.ID) -> fakts_types.Service:
        return fakts_models.Service.objects.get(id=id)
    

    @strawberry_django.field()
    def service_instance(self, info: Info, id: strawberry.ID) -> fakts_types.ServiceInstance:
        return fakts_models.ServiceInstance.objects.get(id=id)


@strawberry.type
class Mutation:
    create_user = strawberry_django.mutation(
        resolver=karakter_mutations.create_user,
    )
    create_comment = strawberry_django.mutation(
        resolver=komment_mutations.create_comment,
    )

    create_room = strawberry_django.mutation(resolver=kammer_mutations.create_room)

    send = strawberry_django.mutation(resolver=kammer_mutations.send)

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
    acknowledge_message = strawberry_django.mutation(
        resolver=karakter_mutations.acknowledge_message
    )

    create_stash = strawberry_django.mutation(
        resolver=pak_mutations.create_stash,
        description="Create a new stash",
    )
    update_stash = strawberry_django.mutation(
        resolver=pak_mutations.update_stash, description="Update a stash"
    )
    add_items_to_stash = strawberry_django.mutation(
        resolver=pak_mutations.add_items_to_stash, description="Add items to a stash"
    )
    delete_stash_items = strawberry_django.mutation(
        resolver=pak_mutations.delete_stash_items,
        description="Delete items from a stash",
    )
    delete_stash = strawberry_django.mutation(
        resolver=pak_mutations.delete_stash,
    )

    create_stream = strawberry_django.mutation(
        resolver=kammer_mutations.create_video_stream
    )
    leave_stream = strawberry_django.mutation(
        resolver=kammer_mutations.leave_video_stream
    )
    join_stream = strawberry_django.mutation(
        resolver=kammer_mutations.join_video_stream
    )


    create_user_defined_service_instance = strawberry_django.mutation(
        resolver=fakts_mutations.create_user_defined_service_instance,
    )


@strawberry.type
class Subscription:
    communications = strawberry.subscription(
        resolver=karakter_subscriptions.communications
    )
    mentions = strawberry.subscription(resolver=komment_subscriptions.mentions)
    room = strawberry.subscription(resolver=kammer_subscriptions.room)


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
    ],  # We really need to register
    # all the types here, otherwise the schema will not be able to resolve them
    # and will throw a cryptic error
)
