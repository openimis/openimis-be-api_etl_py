from abc import ABC


class AuthProvider(ABC):
    """
    Auth provider interface that allow modifying request url, headers and payload to  authorization
    """

    @staticmethod
    def get_auth_header():
        """
        Returns authorization header(s) provided by this authorization method
        """
        return {}


class AuthError(Exception):
    pass