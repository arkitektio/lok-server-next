import jwt
from ekke import errors, structs


def decode_token(token: str, algorithms: list, public_key: str) -> structs.JWTToken:
    """Decode a JWT Token and return a pydantic model wrapping it."""
    try:
        decoded = jwt.decode(token, public_key, algorithms=algorithms)
    except Exception as e:
        raise errors.InvalidJwtTokenError("Error decoding token") from e

    try:
        return structs.JWTToken(**decoded)
    except TypeError as e:
        raise errors.MalformedJwtTokenError("Error decoding token") from e
