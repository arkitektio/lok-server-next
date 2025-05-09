import strawberry_django
from authapp import models

@strawberry_django.type(models.OAuth2Client)
class Oauth2Client:
    id: str
    client_id: str
    
    
    