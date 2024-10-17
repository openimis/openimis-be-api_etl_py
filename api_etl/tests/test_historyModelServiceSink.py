from django.test import TestCase

from api_etl.sinks import HistoryModelServiceSink
from core.test_helpers import create_test_interactive_user
from individual.models import Individual
from individual.services import IndividualService


class HistoryModelServiceSinkTestCase(TestCase):
    _FN_1 = "Test First Name 1"
    _FN_2 = "Test First Name 2"
    _LN_1 = "Test Last Name 1"
    _DOB_1 = "1970-01-01"
    _EXT_1 = {"test_field_1": "Test Value 1"}

    def setUp(self):
        self.user = create_test_interactive_user(username="test_admin")
        self.service = IndividualService(self.user)
        self.sink = HistoryModelServiceSink(self.service)

    def test_success_single(self):
        data = [
            {
                "first_name": self._FN_1,
                "last_name": self._LN_1,
                "dob": self._DOB_1,
                "json_ext": self._EXT_1,
            }
        ]

        self.sink.push(data)

        result = Individual.objects.filter(first_name=self._FN_1, last_name=self._LN_1).count()
        self.assertEquals(result, 1)

    def test_success_multiple(self):
        data = [
            {
                "first_name": self._FN_1,
                "last_name": self._LN_1,
                "dob": self._DOB_1,
                "json_ext": self._EXT_1
            },
            {
                "first_name": self._FN_2,
                "last_name": self._LN_1,
                "dob": self._DOB_1,
                "json_ext": self._EXT_1
            }
        ]

        self.sink.push(data)

        result = Individual.objects.filter(last_name=self._LN_1).count()
        self.assertEquals(result, 2)

    def test_failure(self):
        data = [
            {
                "first_name": self._FN_1,
                "last_name": self._LN_1,
                "dob": self._DOB_1,
                "json_ext": self._EXT_1,
                "non_existent_field": "value",
            }
        ]

        self.assertRaises(self.sink.Error, self.sink.push, data)

    def test_no_rollback_on_fail(self):
        data = [
            {
                "first_name": self._FN_1,
                "last_name": self._LN_1,
                "dob": self._DOB_1,
                "json_ext": self._EXT_1
            },
            {
                "first_name": self._FN_2,
                "last_name": self._LN_1,
                "dob": "invalid",
                "json_ext": self._EXT_1
            }
        ]

        sink = HistoryModelServiceSink(self.service, rollback_on_fail=False)
        sink.push(data)

        result = Individual.objects.filter(last_name=self._LN_1).count()
        self.assertEquals(result, 1)
