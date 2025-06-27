class ConfigurationError(Exception):
    """
    Raised when a configuration error occurs.
    """

    pass


class ConfigurationRequestMalformed(ConfigurationError):
    """
    Raised when a configuration request is malformed
    """

    pass


class InstanceAliasNotFound(ConfigurationError):
    """Raised when an instance alias is not found

    This error is raised when an instance alias is not found. This can
    happen when the alias does not exist or when the alias is not
    associated with a server.
    """

    pass


class BackendError(ConfigurationError):
    """Raised when an error occurs in a backend

    This error is raised when an error occurs in a backend. This can
    happen when a backend is not available or when an error occurs
    while rendering a backend.
    """


class InstanceNotFound(ConfigurationError):
    """Raised when an no instance for a server is found"""

    pass
