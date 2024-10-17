from django.test import TestCase

from api_etl.adapters import ExampleIndividualAdapter


class ExampleIndividualAdapterTestCase(TestCase):
    _FN_1 = "Test First Name 1"
    _FN_2 = "Test First Name 2"
    _LN_1 = "Test Last Name 1"
    _DOB_1 = "1970-01-01"
    _EXT_1 = {"test_field_1": "Test Value 1"}

    def setUp(self):
        self.adapter = ExampleIndividualAdapter()

    def test_transform_success(self):
        data = [{
            'current': 0,
            'rowCount': 1,
            'rows': [{
                "firstName": self._FN_1,
                "lastName": self._LN_1,
                "dateOfBirth": self._DOB_1,
                **self._EXT_1,
            }],
            'total': 100
        }]

        expected = [{
            "first_name": self._FN_1,
            "last_name": self._LN_1,
            "dob": self._DOB_1,
            "json_ext": self._EXT_1
        }]

        actual = self.adapter.transform(data)
        self.assertEquals(actual, expected)

    def test_no_rows(self):
        data = [{
            'current': 0,
            'rowCount': 0,
            'rows': [],
            'total': 0
        }]

        expected = []

        actual = self.adapter.transform(data)
        self.assertEquals(actual, expected)

    def test_no_rows_item(self):
        data = [{
            'current': 0,
            'rowCount': 0,
            'total': 0
        }]

        self.assertRaises(self.adapter.Error, self.adapter.transform, data)
