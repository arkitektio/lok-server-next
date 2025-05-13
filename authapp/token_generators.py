from authlib.oauth2.rfc9068 import JWTBearerTokenGenerator
from joserfc.jwk import RSAKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from django.conf import settings
# Load RSA private key
private_key = serialization.load_pem_private_key(
    settings.PRIVATE_KEY.encode("utf-8"), password=None, backend=default_backend()
)

# Generate JWK from RSA key
jwk = RSAKey.import_key(settings.PRIVATE_KEY)

# Export JWK (public or private depending on use case)
jwk_dict = jwk.as_dict(is_private=False, kid="1")  # use True for full private JWK



print("JWK dict:", jwk_dict)




class MyJWTBearerTokenGenerator(JWTBearerTokenGenerator):
    
    
    def get_jwks(self): 
        return jwk_dict

    def get_extra_claims(self, client, grant_type, user, scope):
        
        if not user:
            user = client.user
            
        if not user:
            raise ValueError("User not found")
        
        
            
        
        #TODO: Impement correct scoping
        return {"roles": [group.name for group in user.groups.all()], "preferred_username": user.username, "sub": user.id, "scope": "openid"}
    
    
    def get_audiences(self, client, user, scope) -> str | list[str]:
        return ["rekuest"]
    