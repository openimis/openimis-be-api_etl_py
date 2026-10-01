from django.apps import AppConfig

from core.rights_declaration import RightsDeclaration

MODULE_NAME = "api_etl"

# Rights, by entity then by action. The module has no model: `apiEtlRule` denotes an
# ETL rule, that is, a service class discovered in `api_etl.services`. `execute` is a
# business action and not an `update`: triggering an ETL pipeline writes into other
# modules (insuree, individual...) without modifying the rule itself. The django name
# stays declarative as long as no model carries `Meta.permissions`.
DJANGO_PERMS = {
    "apiEtlRule": {
        "query": ("api_etl.view_apietlrule", 953001),
        "execute": ("api_etl.execute_apietlrule", 953002),
    },
}

_PERM_CFG = {
    "gql_query_api_etl_rule_perms": ("apiEtlRule", "query"),
    # Dormant right: declared but read nowhere. The mutation that executes a pipeline
    # checks the read right (953001) today and not this one. The separation is laid
    # down here; fixing the call site is another batch of work.
    "gql_mutation_execute_api_etl_rule_perms": ("apiEtlRule", "execute"),
}

RIGHTS = RightsDeclaration(MODULE_NAME, DJANGO_PERMS, _PERM_CFG)

perms = RIGHTS.perms
django_perms = RIGHTS.django_perm_names
configured_perms = RIGHTS.configured
require = RIGHTS.require


DEFAULT_CONFIG = {
    "auth_type": "basic",  # noauth, basic, bearer
    "auth_basic_username": "",  # basic auth username
    "auth_basic_password": "",  # basic auth password
    "auth_bearer_token": "",  # bearer token

    "source_http_method": "",  # valid input for requests.request required
    "source_url": "",
    "source_headers": {},
    "source_batch_size": 50,

    "adapter_first_name_field": "firstName",
    "adapter_last_name_field": "lastName",
    "adapter_dob_field": "dateOfBirth",
    "adapter_location_name_field": "locationName",
    "adapter_location_code_field": "locationCode",

    "sink_model_lookup_field": "json_ext__external_id",
    "sink_update_existing": True,

}


class ApiEtlConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = MODULE_NAME

    auth_type = None
    auth_basic_username = None
    auth_basic_password = None
    auth_bearer_token = None

    source_http_method = None
    source_url = None
    source_headers = None
    source_batch_size = None

    adapter_first_name_field = None
    adapter_last_name_field = None
    adapter_dob_field = None
    adapter_location_name_field = None
    adapter_location_code_field = None

    sink_model_lookup_field = None
    sink_update_existing = None

    # Rights: constants, no longer overridable. They go neither through DEFAULT_CFG
    # nor through ready(): `ModuleConfiguration.get_or_default` now ignores any
    # `_perms` key stored in the database.
    gql_query_api_etl_rule_perms = RIGHTS.perms("apiEtlRule", "query")
    gql_mutation_execute_api_etl_rule_perms = RIGHTS.perms("apiEtlRule", "execute")

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
