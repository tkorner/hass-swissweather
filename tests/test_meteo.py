"""Tests for MeteoSwiss HTTP handling."""

import unittest
from unittest.mock import MagicMock, Mock, patch

from .module_loader import load_module


meteo = load_module("meteo")


class MeteoClientTest(unittest.TestCase):
    def setUp(self):
        self.client = meteo.MeteoClient()

    def test_forecast_request_has_timeout_and_checks_http_status(self):
        response = Mock()
        response.json.return_value = {"forecast": []}

        with patch.object(meteo.requests, "get", return_value=response) as get:
            result = self.client._get_forecast_json("8001", "en")

        self.assertEqual(result, {"forecast": []})
        get.assert_called_once()
        self.assertEqual(
            get.call_args.kwargs["timeout"], meteo.REQUEST_TIMEOUT
        )
        response.raise_for_status.assert_called_once_with()

    def test_forecast_http_error_returns_none(self):
        response = Mock()
        response.raise_for_status.side_effect = meteo.requests.HTTPError("failed")

        with patch.object(meteo.requests, "get", return_value=response):
            result = self.client._get_forecast_json("8001", "en")

        self.assertIsNone(result)

    def test_current_weather_http_error_returns_none(self):
        # An HTML error page must not be parsed as CSV; without the status
        # check this raised KeyError: 'Station/Location'.
        response = MagicMock()
        response.__enter__.return_value = response
        response.iter_lines.return_value = [b"<html>503 Service Unavailable</html>"]
        response.raise_for_status.side_effect = meteo.requests.HTTPError("503")

        with patch.object(meteo.requests, "get", return_value=response):
            result = self.client.get_current_weather_for_station("SMA")

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
