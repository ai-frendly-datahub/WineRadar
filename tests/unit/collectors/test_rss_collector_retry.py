# pyright: reportPrivateUsage=false
from __future__ import annotations
from typing import Optional

from unittest.mock import Mock, patch

import pytest
import requests

from collectors.rss_collector import RSSCollector


class _BytesResponse:
    def __init__(self, content: bytes, error: Optional[Exception] = None) -> None:
        self.content: bytes = content
        self._error: Optional[Exception] = error

    def raise_for_status(self) -> None:
        if self._error:
            raise self._error


class TestRSSCollectorRetryLogic:
    @staticmethod
    def _create_collector() -> RSSCollector:
        source_meta = {
            "id": "media_sample_rss",
            "name": "Sample RSS Source",
            "type": "media",
            "country": "GB",
            "continent": "OLD_WORLD",
            "region": "Europe/Western/UK",
            "producer_role": "expert_media",
            "trust_tier": "T2_expert",
            "info_purpose": ["P1_daily_briefing"],
            "collection_tier": "C1_rss",
            "supports_rss": True,
            "requires_login": False,
            "content_type": "news_review",
            "language": "en",
            "config": {"list_url": "https://example.com/feed"},
        }
        return RSSCollector(source_meta)

    @patch("collectors.rss_collector.requests.get")
    def test_retry_on_timeout(self, mock_get: Mock) -> None:
        collector = self._create_collector()

        mock_get.side_effect = [
            requests.exceptions.Timeout("timeout"),
            requests.exceptions.Timeout("timeout"),
            _BytesResponse(b"<rss></rss>"),
        ]

        with patch("time.sleep", return_value=None):
            content = collector._default_fetcher("https://example.com/feed")

        assert content == b"<rss></rss>"
        assert mock_get.call_count == 3

    @patch("collectors.rss_collector.requests.get")
    def test_retry_on_5xx_error(self, mock_get: Mock) -> None:
        collector = self._create_collector()

        fail_response = _BytesResponse(
            b"<rss></rss>",
            error=requests.exceptions.HTTPError("500 Server Error"),
        )
        success_response = _BytesResponse(b"<rss></rss>")
        mock_get.side_effect = [fail_response, fail_response, success_response]

        with patch("time.sleep", return_value=None):
            content = collector._default_fetcher("https://example.com/feed")

        assert content == b"<rss></rss>"
        assert mock_get.call_count == 3

    @patch("collectors.rss_collector.requests.get")
    def test_max_retries_exceeded(self, mock_get: Mock) -> None:
        collector = self._create_collector()
        mock_get.side_effect = requests.exceptions.Timeout("timeout")

        with patch("time.sleep", return_value=None):
            with pytest.raises(requests.exceptions.Timeout):
                _ = collector._default_fetcher("https://example.com/feed")

        assert mock_get.call_count == 3

    @patch("collectors.rss_collector.requests.get")
    def test_connection_error_recovery(self, mock_get: Mock) -> None:
        collector = self._create_collector()

        mock_get.side_effect = [
            requests.exceptions.ConnectionError("connection error"),
            _BytesResponse(b"<rss></rss>"),
        ]

        with patch("time.sleep", return_value=None):
            content = collector._default_fetcher("https://example.com/feed")

        assert content == b"<rss></rss>"
        assert mock_get.call_count == 2
