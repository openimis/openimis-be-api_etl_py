from django.apps import AppConfig

DEFAULT_CONFIG = {
    "auth_type": "noauth",  # noauth, basic, bearer
    "auth_basic_username": "",  # basic auth username
    "auth_basic_password": "",  # basic auth password
    "auth_bearer_token": "",  # bearer token
}


class ApiEtlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_etl'

    auth_type = None

    auth_basic_username = None
    auth_basic_password = None

    auth_bearer_token = None

    @classmethod
    def _load_config(cls, cfg):
        """
        Load all config fields that match current AppConfig class fields, all custom fields have to be loaded separately
        """
        for field in cfg:
            if hasattr(ApiEtlConfig, field):
                setattr(ApiEtlConfig, field, cfg[field])

    def ready(self):
        from core.models import ModuleConfiguration

        cfg = ModuleConfiguration.get_or_default(self.name, DEFAULT_CONFIG)
        self._load_config(cfg)
