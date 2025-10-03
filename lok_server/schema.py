from typing import Any, AsyncGenerator, Type

import strawberry
import strawberry_django
from kante.types import Info
from fakts import types as fakts_types
from fakts.graphql import mutations as fakts_mutations
from fakts.graphql import queries as fakts_queries
from fakts.graphql import subscriptions as fakts_subscriptions
from fakts import models as fakts_models
from karakter import types as karakter_types
from karakter import models as karakter_models
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
from karakter.datalayer import DatalayerExtension
from strawberry_django.optimizer import DjangoOptimizerExtension
from authapp.extension import AuthAppExtension
import kante



@strawberry.type
class Query:
    stashes: list[pak_types.Stash] = strawberry_django.field()
    stash_items: list[pak_types.StashItem] = strawberry_django.field()
    my_stashes = strawberry_django.field(resolver=pak_queries.my_stashes)

    organizations: list[karakter_types.Organization] = kante.django_field()

    mycontext = strawberry_django.field(resolver=karakter_queries.mycontext)

    apps: list[fakts_types.App] = strawberry_django.field()
    releases: list[fakts_types.Release] = strawberry_django.field()
    clients: list[fakts_types.Client] = strawberry_django.field()
    users: list[karakter_types.User] = strawberry_django.field()
    roles: list[karakter_types.Role] = strawberry_django.field()
    groups: list[karakter_types.Group] = strawberry_django.field()
    comments: list[komment_types.Comment] = strawberry_django.field()
    services: list[fakts_types.Service] = strawberry_django.field()
    service_instances: list[fakts_types.ServiceInstance] = strawberry_django.field()

    user = strawberry_django.field(resolver=karakter_queries.user)
    me = strawberry_django.field(resolver=karakter_queries.me)
    group = strawberry_django.field(resolver=karakter_queries.group)
    mygroups = strawberry_django.field(resolver=karakter_queries.mygroups)

    app = strawberry_django.field(resolver=fakts_queries.app)
    release = strawberry_django.field(resolver=fakts_queries.release)
    client = strawberry_django.field(resolver=fakts_queries.client)
    my_managed_clients = strawberry_django.field(resolver=fakts_queries.my_managed_clients)
    layers: list[fakts_types.Layer] = strawberry_django.field()

    scopes = strawberry_django.field(resolver=fakts_queries.scopes)

    comment = strawberry_django.field(resolver=komment_queries.comment)
    comments_for = strawberry_django.field(resolver=komment_queries.comments_for)
    my_mentions = strawberry_django.field(resolver=komment_queries.my_mentions)
    redeem_tokens: list[fakts_types.RedeemToken] = strawberry_django.field()

    stash: pak_types.Stash = strawberry_django.field(resolver=pak_queries.stash)
    stash_item: pak_types.StashItem = strawberry_django.field(resolver=pak_queries.stash_item)
    my_active_messages = strawberry_django.field(resolver=karakter_queries.my_active_messages)
    message = strawberry_django.field(resolver=karakter_queries.message)
    
    @kante.django_field()
    def hallo(self, info: Info) -> str:
        print("hallosss")
        return "hallo"

    @kante.django_field(name="service")
    def detail_service(self, info: Info, id: strawberry.ID) -> fakts_types.Service:
        return fakts_models.Service.objects.get(id=id)

    @kante.django_field()
    def role(self, info: Info, id: strawberry.ID) -> karakter_types.Role:
        return karakter_models.Role.objects.get(id=id)

    @kante.django_field()
    def organization(self, info: Info, id: strawberry.ID) -> karakter_types.Organization:
        return karakter_models.Organization.objects.get(id=id)
    
    
    @kante.django_field()
    def redeem_token(self, info: Info, id: strawberry.ID) -> fakts_types.RedeemToken:
        return fakts_models.RedeemToken.objects.get(id=id)
    
    @kante.django_field()
    def my_redeem_tokens(self, info: Info) -> list[fakts_types.RedeemToken]:
        return fakts_models.RedeemToken.objects.filter(user=info.context.request.user, organization=info.context.request.organization)
    
    

    @kante.django_field()
    def layer(self, info: Info, id: strawberry.ID) -> fakts_types.Layer:
        return fakts_models.Layer.objects.get(id=id)

    @kante.django_field()
    def service_instance(self, info: Info, id: strawberry.ID) -> fakts_types.ServiceInstance:
        return fakts_models.ServiceInstance.objects.get(id=id)


@strawberry.type
class Mutation:
    create_user = strawberry_django.mutation(
        resolver=karakter_mutations.create_user,
    )

    add_user_to_organization = strawberry_django.mutation(
        resolver=karakter_mutations.add_user_to_organization,
    )

    create_comment = strawberry_django.mutation(
        resolver=komment_mutations.create_comment,
    )
    register_com_channel = strawberry_django.mutation(
        resolver=karakter_mutations.register_com_channel,
    )
    notify_user = strawberry_django.mutation(
        resolver=karakter_mutations.notify_user,
    )
    
    create_redeem_token = strawberry_django.mutation(
        resolver=fakts_mutations.create_redeem_token,
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
    render = strawberry_django.mutation(
        resolver=fakts_mutations.render_composition,
    )
    acknowledge_message = strawberry_django.mutation(resolver=karakter_mutations.acknowledge_message)

    create_stash = strawberry_django.mutation(
        resolver=pak_mutations.create_stash,
        description="Create a new stash",
    )
    update_stash = strawberry_django.mutation(resolver=pak_mutations.update_stash, description="Update a stash")
    add_items_to_stash = strawberry_django.mutation(resolver=pak_mutations.add_items_to_stash, description="Add items to a stash")
    delete_stash_items = strawberry_django.mutation(
        resolver=pak_mutations.delete_stash_items,
        description="Delete items from a stash",
    )
    delete_stash = strawberry_django.mutation(
        resolver=pak_mutations.delete_stash,
    )
    create_service_instance = strawberry_django.mutation(
        resolver=fakts_mutations.create_service_instance,
    )

    update_service_instance = strawberry_django.mutation(
        resolver=fakts_mutations.update_service_instance,
    )

    create_instance_alias = strawberry_django.mutation(
        resolver=fakts_mutations.create_instance_alias,
    )
    update_instance_alias = strawberry_django.mutation(
        resolver=fakts_mutations.update_instance_alias,
    )

    request_media_upload = strawberry_django.mutation(
        resolver=karakter_mutations.request_media_upload,
    )

    update_profile = strawberry_django.mutation(
        resolver=karakter_mutations.update_profile,
    )
    create_profile = strawberry_django.mutation(
        resolver=karakter_mutations.create_profile,
    )

    update_group_profile = strawberry_django.mutation(
        resolver=karakter_mutations.update_group_profile,
    )
    create_group_profile = strawberry_django.mutation(
        resolver=karakter_mutations.create_group_profile,
    )


@strawberry.type
class Subscription:
    communications = strawberry.subscription(resolver=karakter_subscriptions.communications)
    mentions = strawberry.subscription(resolver=komment_subscriptions.mentions)


schema = kante.Schema(
    query=Query,
    subscription=Subscription,
    mutation=Mutation,
    extensions=[DjangoOptimizerExtension, AuthAppExtension, DatalayerExtension],
    types=[
        komment_types.Descendant,
        komment_types.MentionDescendant,
        komment_types.ParagraphDescendant,
        komment_types.LeafDescendant,
    ],  # We really need to register
    # all the types here, otherwise the schema will not be able to resolve them
    # and will throw a cryptic error
)
