from django.core.exceptions import PermissionDenied


class EkkeError(Exception):
    """ The base error for all Ekke Errors"""
    pass


class EkkePermissionDenied(PermissionDenied):
    """ The base error for all Ekke Permission Errors.
    Inherits from Django's PermissionDenied"""
    pass


class EkkeTokenExpired(EkkePermissionDenied):
    """ If the token is expired, this error is raised."""
    pass


class JwtTokenError(EkkePermissionDenied):
    """ The base error for all JWT Token Errors."""
    pass


class MalformedJwtTokenError(JwtTokenError):
    """ If the token is malformed, this error is raised."""
    pass


class InvalidJwtTokenError(JwtTokenError):
    """ If the token is invalid, this error is raised."""
    pass


class UserNotFound(EkkePermissionDenied):
    """ If the user is not found, this error is raised."""
    pass
