from typing import Literal

from api_etl.auth_provider.base import AuthError
from api_etl.auth_provider.basicAuthProvider import BasicAuthProvider
from api_etl.auth_provider.bearerAuthProvider import BearerAuthProvider
from api_etl.auth_provider.noAuthAuthProvider import NoAuthProvider

_auth_config_mapping = {
    "noauth": NoAuthProvider,
    "basic": BasicAuthProvider,
    "bearer": BearerAuthProvider,
}


def get_auth_provider(auth_type: Literal["noauth", "basic", "bearer"]):
    if auth_type not in _auth_config_mapping:
        AuthError(f"Unknown auth type: {auth_type}")
    return _auth_config_mapping[auth_type]
