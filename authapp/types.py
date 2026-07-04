import strawberry
import strawberry_django
from authapp import models


@strawberry_django.order_type(models.OAuth2Client)
class OAuth2ClientOrdering:
    id: strawberry.auto


@strawberry_django.type(models.OAuth2Client, ordering=OAuth2ClientOrdering)
class Oauth2Client:
    id: str
    client_id: str
    
    
    