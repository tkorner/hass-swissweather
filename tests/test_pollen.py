"""Tests for MeteoSwiss pollen HTTP handling."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from .module_loader import load_module


meteo = load_module("meteo")
pollen = load_module("pollen")


class PollenClientTest(unittest.TestCase):
    def setUp(self):
        self.client = pollen.PollenClient()

    def test_pollen_request_has_timeout_and_checks_http_status(self):
        response = Mock()
        response.json.return_value = {
            "stations": [{"id": "PBS", "current": {"value": "12", "date": 0}}]
        }

        with patch.object(pollen.requests, "get", return_value=response) as get:
            value, _ = self.client.get_current_pollen_for_station_type("PBS", "birke")

        self.assertEqual(value, 12.0)
        self.assertEqual(get.call_args.kwargs["timeout"], meteo.REQUEST_TIMEOUT)
        response.raise_for_status.assert_called_once_with()

    def test_pollen_http_error_returns_none(self):
        response = Mock()
        response.raise_for_status.side_effect = pollen.requests.HTTPError("503")

        with patch.object(pollen.requests, "get", return_value=response):
            result = self.client.get_current_pollen_for_station_type("PBS", "birke")

        self.assertEqual(result, (None, None))
        response.json.assert_not_called()

    def test_pollen_station_list_http_error_yields_no_rows(self):
        response = MagicMock()
        response.__enter__.return_value = response
        # Without the status check, every HTML line after the first would be
        # yielded as a bogus station row.
        response.iter_lines.return_value = [
            b"<html>", b"<body>503 Service Unavailable</body>", b"</html>"
        ]
        response.raise_for_status.side_effect = pollen.requests.HTTPError("503")

        with patch.object(pollen.requests, "get", return_value=response):
            rows = list(self.client._get_csv_dictionary_for_url("https://example.invalid"))

        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
