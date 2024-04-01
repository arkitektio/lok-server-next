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


class NoConfigurationFound(Exception):
    pass


class BackendNotAvailable(ConfigurationError):
    pass



class BackendError(ConfigurationError):
    """Raised when an error occurs in a backend

    This error is raised when an error occurs in a backend. This can
    happen when a backend is not available or when an error occurs
    while rendering a backend.
    """
