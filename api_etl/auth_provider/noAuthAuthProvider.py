from api_etl.auth_provider.base import AuthProvider


class NoAuthProvider(AuthProvider):
    """
    Implementation of AuthProvider Interface that does not provide any authorization
    """
    pass
