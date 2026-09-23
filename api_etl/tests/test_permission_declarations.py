"""
Garde-fous sur la declaration des droits d'api_etl.

Meme structure que `claim` et `core` : `DJANGO_PERMS` par entite puis par action, et
`_PERM_CFG` qui en derive les cles de config. La particularite d'api_etl est qu'il n'a
aucun modele : `apiEtlRule` designe une classe de service decouverte dynamiquement dans
`api_etl.services`, il n'y a donc pas de point d'acces `Model.get_rights` a verrouiller.

Ce qui est verrouille ici :
  * les identifiants 953001/953002, tels que deployes et tels que les porte
    `permissions_map.json` - en changer un retire l'acces aux roles qui le detiennent ;
  * une cle de config sans attribut de classe n'est jamais chargee par `_load_config`
    et sa lecture leve AttributeError - le droit devient inapplicable ;
  * `has_perms([])` renvoie True, donc une liste vide accorde a tous.
"""

import json
import os

from django.test import TestCase

from api_etl.apps import (
    DJANGO_PERMS,
    ApiEtlConfig,
    _PERM_CFG,
    configured_perms,
    django_perms,
    perms,
)

# Les identifiants tels que deployes. En changer un est incompatible avec les roles
# existants : il faut mettre ce test a jour *et* accorder le nouveau droit.
EXPECTED_RIGHTS = {
    "gql_query_api_etl_rule_perms": ["953001"],
    "gql_mutation_execute_api_etl_rule_perms": ["953002"],
}

# Les cles de `permissions_map.json` qui portent ces memes identifiants.
EXPECTED_MAP_ENTRIES = {
    "api_etl.api_etl_rule": "953001",
    "api_etl.execute_api_etl_rule": "953002",
}


def _load_permissions_map():
    """`permissions_map.json` vit dans l'assemblage, pas dans le paquet."""
    from django.conf import settings

    candidates = [
        os.path.join(str(settings.BASE_DIR), "permissions_map.json"),
        os.path.join(os.path.dirname(str(settings.BASE_DIR)), "permissions_map.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as handle:
                return json.load(handle)
    return None


class ApiEtlPermissionDeclarationTestCase(TestCase):
    def test_right_ids_unchanged(self):
        self.assertEqual(
            {key: getattr(ApiEtlConfig, key) for key in EXPECTED_RIGHTS},
            EXPECTED_RIGHTS,
        )

    def test_perm_cfg_covers_every_declared_action(self):
        declared = {
            (entity, action)
            for entity, actions in DJANGO_PERMS.items()
            for action in actions
        }
        self.assertEqual(set(_PERM_CFG.values()), declared)

    def test_perm_cfg_matches_config_attributes(self):
        """`_load_config` ignore les cles sans attribut de classe."""
        missing = [key for key in _PERM_CFG if not hasattr(ApiEtlConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        empty = [key for key in _PERM_CFG if not getattr(ApiEtlConfig, key)]
        self.assertEqual(empty, [])

    def test_attributes_carry_the_declared_right(self):
        """
        Les droits sont des constantes posees depuis DJANGO_PERMS : l'attribut doit
        valoir la declaration, sans passer par la config.
        """
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(ApiEtlConfig, key), perms(entity, action))

    def test_query_and_execute_are_distinct_rights(self):
        """
        La lecture d'une regle ETL et son execution ne sont pas le meme droit. Le site
        d'appel de la mutation controle encore 953001 (faille connue, autre lot) ; la
        declaration, elle, doit garder les deux separes.
        """
        self.assertNotEqual(
            perms("apiEtlRule", "query"), perms("apiEtlRule", "execute")
        )

    def test_no_shared_right_ids(self):
        """Aucun partage d'identifiant n'est prevu dans ce module."""
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (_, right_id) in actions.items():
                seen.setdefault(right_id, []).append((entity, action))
        shared = {rid: who for rid, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_are_unique(self):
        seen = {}
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                seen.setdefault(name, []).append(f"{entity}.{action}")
        shared = {name: who for name, who in seen.items() if len(who) > 1}
        self.assertEqual(shared, {})

    def test_django_permission_names_use_the_app_label(self):
        """L'app_label dans cet assemblage est `api_etl`, pas le nom du paquet pip."""
        for entity, actions in DJANGO_PERMS.items():
            for action, (name, _) in actions.items():
                with self.subTest(entity=entity, action=action):
                    self.assertTrue(name.startswith("api_etl."))

    def test_unknown_entity_or_action_raises(self):
        with self.assertRaises(KeyError):
            perms("nosuchentity", "query")
        with self.assertRaises(KeyError):
            perms("apiEtlRule", "nosuchaction")
        with self.assertRaises(KeyError):
            django_perms("apiEtlRule", "nosuchaction")

    def test_configured_reads_the_configured_value_not_the_declared_default(self):
        """
        ModuleConfiguration peut surcharger un droit ; un controle doit lire la valeur
        configuree, la ou `perms()` renvoie le defaut declare.
        """
        original = ApiEtlConfig.gql_query_api_etl_rule_perms
        try:
            ApiEtlConfig.gql_query_api_etl_rule_perms = ["999999"]
            self.assertEqual(configured_perms("apiEtlRule", "query"), ["999999"])
            self.assertEqual(perms("apiEtlRule", "query"), ["953001"])
        finally:
            ApiEtlConfig.gql_query_api_etl_rule_perms = original

    def test_configured_returns_none_for_an_undeclared_action(self):
        """None signifie "aucune regle" : l'appelant doit echouer ferme."""
        self.assertIsNone(configured_perms("apiEtlRule", "nosuchaction"))

    def test_ids_match_permissions_map(self):
        """La carte des droits de l'assemblage doit porter les memes entiers."""
        mapping = _load_permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json introuvable dans cet assemblage")
        for key, right_id in EXPECTED_MAP_ENTRIES.items():
            with self.subTest(key=key):
                self.assertEqual(str(mapping.get(key)), right_id)
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        self.assertEqual(set(EXPECTED_MAP_ENTRIES.values()), declared_ids)
