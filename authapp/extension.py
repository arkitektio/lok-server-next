from typing import AsyncIterator, Iterator, Union, cast
from strawberry.extensions import SchemaExtension
from kante.context import WsContext, HttpContext
from authentikate.strawberry.extension import AuthentikateExtension, UserModel, JWTToken
from karakter.models import User, Organization, Membership
from fakts.models import Client
from authapp.models import OAuth2Client


async def expand_user_from_token(token: str):
    """Expand the user from the token"""
    # Implement your logic to expand the user from the token
    pass


class AuthAppExtension(AuthentikateExtension):
    """This is the extension class for directly authenticating users and
    clients from the token or header. It sets the user and client in the"""

    async def aexpand_token_context(self, token: JWTToken) -> tuple[User, Client, Organization, Membership]:
        """Expand the full auth context for a token using this project's models.

        authentikate (v2) drives ``on_operation`` through this single method
        rather than the per-entity ``aexpand_*`` helpers, so we compose them
        here to keep authentication backed by the karakter/fakts models.
        """
        organization = await self.aexpand_organization_from_token(token)
        user = await self.aexpand_user_from_token(token)
        client = await self.aexpand_client_from_token(token)
        membership = await self.aexpand_membership_from_user_and_organization(user, organization, token)
        return (cast(User, user), client, organization, membership)

    async def aexpand_user_from_token(self, token: JWTToken) -> "UserModel":
        """Expand a user from the provided JWT token"""

        return cast("UserModel", await User.objects.aget(id=token.sub))

    async def aexpand_client_from_token(self, token: JWTToken) -> "Client":
        """Expand a client from the provided JWT token"""

        return cast("Client", await OAuth2Client.objects.prefetch_related("client").aget(client_id=token.client_id)).client

    async def aexpand_organization_from_token(self, token: JWTToken) -> "Organization":
        """Expand an organization from the provided JWT token"""

        # Assuming the organization is stored in the token
        return cast("Organization", await Organization.objects.aget(slug=token.active_org))

    async def aexpand_membership_from_user_and_organization(self, user: "UserModel", organization: "Organization", token: JWTToken) -> "Membership":
        """Expand membership from user and organization"""
        membership = await user.memberships.aget(organization=organization)
        return membership
