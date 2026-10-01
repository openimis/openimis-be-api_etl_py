"""
Guard rails on api_etl's rights declaration.

Same structure as `claim` and `core`: `DJANGO_PERMS` by entity then by action, and
`_PERM_CFG` deriving the config keys from it. What is particular to api_etl is that it
has no model at all: `apiEtlRule` denotes a service class discovered dynamically in
`api_etl.services`, so there is no `Model.get_rights` access point to lock down.

What is locked down here:
  * the identifiers 953001/953002, as deployed and as `permissions_map.json` carries
    them - changing one withdraws access from the roles that hold it;
  * a config key with no class attribute is never loaded by `_load_config` and reading
    it raises AttributeError - the right becomes unenforceable;
  * `has_perms([])` returns True, so an empty list grants to everybody.
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

# The identifiers as deployed. Changing one is incompatible with the existing roles:
# this test has to be updated *and* the new right granted.
EXPECTED_RIGHTS = {
    "gql_query_api_etl_rule_perms": ["953001"],
    "gql_mutation_execute_api_etl_rule_perms": ["953002"],
}

# The `permissions_map.json` keys that carry these same identifiers.
EXPECTED_MAP_ENTRIES = {
    "api_etl.api_etl_rule": "953001",
    "api_etl.execute_api_etl_rule": "953002",
}


def _load_permissions_map():
    """`permissions_map.json` lives in the assembly, not in the package."""
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
        """`_load_config` ignores the keys with no class attribute."""
        missing = [key for key in _PERM_CFG if not hasattr(ApiEtlConfig, key)]
        self.assertEqual(missing, [])

    def test_no_right_list_is_empty(self):
        empty = [key for key in _PERM_CFG if not getattr(ApiEtlConfig, key)]
        self.assertEqual(empty, [])

    def test_attributes_carry_the_declared_right(self):
        """
        The rights are constants set from DJANGO_PERMS: the attribute must equal the
        declaration, without going through the config.
        """
        for key, (entity, action) in _PERM_CFG.items():
            with self.subTest(key=key):
                self.assertEqual(getattr(ApiEtlConfig, key), perms(entity, action))

    def test_query_and_execute_are_distinct_rights(self):
        """
        Reading an ETL rule and executing it are not the same right. The mutation's
        call site still checks 953001 (a known hole, another batch of work); the
        declaration itself must keep the two separate.
        """
        self.assertNotEqual(
            perms("apiEtlRule", "query"), perms("apiEtlRule", "execute")
        )

    def test_no_shared_right_ids(self):
        """No identifier sharing is intended in this module."""
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
        """The app_label in this assembly is `api_etl`, not the pip package name."""
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
        ModuleConfiguration may override a right; a check must read the configured
        value, where `perms()` returns the declared default.
        """
        original = ApiEtlConfig.gql_query_api_etl_rule_perms
        try:
            ApiEtlConfig.gql_query_api_etl_rule_perms = ["999999"]
            self.assertEqual(configured_perms("apiEtlRule", "query"), ["999999"])
            self.assertEqual(perms("apiEtlRule", "query"), ["953001"])
        finally:
            ApiEtlConfig.gql_query_api_etl_rule_perms = original

    def test_configured_returns_none_for_an_undeclared_action(self):
        """None means "no rule": the caller must fail closed."""
        self.assertIsNone(configured_perms("apiEtlRule", "nosuchaction"))

    def test_ids_match_permissions_map(self):
        """The assembly's rights map must carry the same integers."""
        mapping = _load_permissions_map()
        if mapping is None:
            self.skipTest("permissions_map.json not found in this assembly")
        for key, right_id in EXPECTED_MAP_ENTRIES.items():
            with self.subTest(key=key):
                self.assertEqual(str(mapping.get(key)), right_id)
        declared_ids = {
            str(right_id)
            for actions in DJANGO_PERMS.values()
            for _, right_id in actions.values()
        }
        self.assertEqual(set(EXPECTED_MAP_ENTRIES.values()), declared_ids)
