class InvalidAuthenticationError(ValueError):
    """Raised if the auth details you pass into '.start()' are incorrectly formatted."""
    pass


class ConnectionFailedError(Exception):
    """Raised if the connection to Beam fails - this is often due to your auth details being incorrect."""
    pass
