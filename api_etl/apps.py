from django.apps import AppConfig

from core.rights_declaration import RightsDeclaration

MODULE_NAME = "api_etl"

# Droits, par entite puis par action. Le module n'a pas de modele : `apiEtlRule` designe
# une regle ETL, c'est-a-dire une classe de service decouverte dans `api_etl.services`.
# `execute` est une action metier et non un `update` : declencher un pipeline ETL ecrit
# dans d'autres modules (insuree, individual...) sans modifier la regle elle-meme.
# Le nom django reste declaratif tant qu'aucun modele ne porte `Meta.permissions`.
DJANGO_PERMS = {
    "apiEtlRule": {
        "query": ("api_etl.view_apietlrule", 953001),
        "execute": ("api_etl.execute_apietlrule", 953002),
    },
}

_PERM_CFG = {
    "gql_query_api_etl_rule_perms": ("apiEtlRule", "query"),
    # Droit dormant : declare mais lu nulle part. La mutation qui execute un pipeline
    # controle aujourd'hui le droit de lecture (953001) et non celui-ci. La separation
    # est posee ici ; corriger le site d'appel est un autre lot.
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

    # Droits: constantes, plus surchargeables. Ils ne passent plus par le
    # DEFAULT_CFG ni par ready(): `ModuleConfiguration.get_or_default` ignore
    # desormais toute cle `_perms` stockee en base.
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
