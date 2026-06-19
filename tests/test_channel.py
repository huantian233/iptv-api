"""Unit tests for utils/channel.py"""

import os
import sys
from collections import defaultdict
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.channel import (
    format_channel_data,
    check_channel_need_frozen,
)


class TestFormatChannelData:
    def test_basic_url(self):
        result = format_channel_data("http://example.com/stream", "subscribe")
        assert result["url"] == "http://example.com/stream"
        assert result["origin"] == "subscribe"
        assert result["ipv_type"] is None
        assert result["extra_info"] == ""

    def test_url_with_info(self):
        result = format_channel_data("http://example.com/stream$some_info", "local")
        assert result["url"] == "http://example.com/stream"
        assert result["extra_info"] == "some_info"
        assert result["origin"] == "local"

    def test_url_with_whitelist_marker(self):
        result = format_channel_data("http://example.com/stream$!info", "subscribe")
        assert result["url"] == "http://example.com/stream"
        assert result["origin"] == "whitelist"
        assert result["extra_info"] == "info"

    def test_id_is_hash_of_url(self):
        result = format_channel_data("http://example.com/stream", "local")
        assert result["id"] == hash("http://example.com/stream")

    def test_host_extracted(self):
        result = format_channel_data("http://example.com/path/stream.m3u8", "subscribe")
        assert result["host"] is not None
        assert "example.com" in result["host"]


class TestCheckChannelNeedFrozen:
    def test_delay_minus_one(self):
        info = {"delay": -1, "speed": 5}
        assert check_channel_need_frozen(info) is True

    def test_speed_zero(self):
        info = {"delay": 100, "speed": 0}
        assert check_channel_need_frozen(info) is True

    def test_normal_channel(self):
        info = {"delay": 100, "speed": 5}
        assert check_channel_need_frozen(info) is False

    def test_low_resolution(self):
        info = {"delay": 100, "speed": 5, "resolution": "320x240"}
        assert check_channel_need_frozen(info) is True

    def test_high_resolution(self):
        info = {"delay": 100, "speed": 5, "resolution": "3840x2160"}
        assert check_channel_need_frozen(info) is False

    def test_no_delay_key(self):
        info = {"speed": 5}
        assert check_channel_need_frozen(info) is False

    def test_no_speed_key(self):
        info = {"delay": 100}
        assert check_channel_need_frozen(info) is True
