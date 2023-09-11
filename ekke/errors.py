from django.core.exceptions import PermissionDenied


class EkkeError(Exception):
    pass


class EkkePermissionDenied(PermissionDenied):
    pass


class EkkeTokenExpired(EkkePermissionDenied):
    pass


class JwtTokenError(EkkePermissionDenied):
    pass


class MalformedJwtTokenError(JwtTokenError):
    pass


class InvalidJwtTokenError(JwtTokenError):
    pass


class UserNotFound(EkkePermissionDenied):
    pass
