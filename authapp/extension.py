from typing import AsyncIterator, Iterator, Union
from strawberry.extensions import SchemaExtension
from kante.context import WsContext, HttpContext
from authentikate.strawberry.extension import AuthentikateExtension, ClientModel, UserModel, JWTToken
from karakter.models import User
from authapp.models import OAuth2Client


async def expand_user_from_token(token: str):
    
    """ Expand the user from the token """
    # Implement your logic to expand the user from the token
    pass












class AuthAppExtension(AuthentikateExtension):
    """ This is the extension class for directly authenticating users and
    clients from the token or header. It sets the user and client in the"""
    
    async def aexpand_user_from_token(self, token: JWTToken) -> "UserModel":
        """ Expand a user from the provided JWT token """
        
        return await User.objects.aget(id=token.sub)
       
       
    async def aexpand_client_from_token(self, token: JWTToken) -> "ClientModel":
        """ Expand a client from the provided JWT token """
        
        return await OAuth2Client.objects.aget(client_id=token.client_id)
        
        
        
    
       

        