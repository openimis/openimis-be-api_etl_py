import logging
from unittest import skipIf

from django.test import TestCase

from api_etl.apps import ApiEtlConfig
from api_etl.services.exampleIndividualETLService import ExampleIndividualETLService
from core.test_helpers import create_test_interactive_user
from individual.models import Individual

logger = logging.getLogger(__name__)


class ETLServiceTestCase(TestCase):
    @skipIf(ApiEtlConfig.skip_integration_test,
            "This is a full integration test for the example API and should not be run with the default test suite")
    def test_1(self):
        user = create_test_interactive_user(username="test_admin")

        service = ExampleIndividualETLService(user)
        service.execute()

        logging.info("Successfully imported %s individuals", Individual.objects.count())
