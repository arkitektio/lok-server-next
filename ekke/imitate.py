from ekke.structs import Auth, EkkeSettings
from django.contrib.auth import get_user_model


def imitate_user(auth: Auth, imitate_id: str, settings: EkkeSettings) -> Auth:
    sub, iss = imitate_id.split("@")
    user = get_user_model().objects.get(sub=sub, iss=iss)

    if auth.user.has_perm(settings.imitate_permission, user):
        auth.user = user
        return auth

    else:
        raise PermissionError("User does not have permission to imitate this user")
