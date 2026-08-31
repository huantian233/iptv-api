"""Unit tests for utils/config.py"""

import configparser
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import ConfigManager, get_resolution_value, resource_path


class TestGetResolutionValue:
    def test_standard_resolution(self):
        assert get_resolution_value("1920x1080") == 1920 * 1080

    def test_capital_x(self):
        assert get_resolution_value("1920X1080") == 1920 * 1080

    def test_asterisk(self):
        assert get_resolution_value("1920*1080") == 1920 * 1080

    def test_no_match(self):
        assert get_resolution_value("invalid") == 0

    def test_720p(self):
        assert get_resolution_value("1280x720") == 1280 * 720

    def test_4k(self):
        assert get_resolution_value("3840x2160") == 3840 * 2160


class TestResourcePath:
    def test_returns_absolute_path(self):
        result = resource_path("some/path.txt")
        assert os.path.isabs(result)

    def test_existing_file(self):
        result = resource_path("utils/config.py")
        assert os.path.exists(result)

    def test_persistent_flag(self):
        result = resource_path("nonexistent/path.txt", persistent=True)
        assert "nonexistent/path.txt" in result


class TestConfigManager:
    @pytest.fixture
    def config_with_file(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.ini"
        config_file.write_text(
            "[Settings]\n"
            "open_update = True\n"
            "urls_limit = 15\n"
            "min_speed = 1.0\n"
            "min_resolution = 1280x720\n"
            "ipv_type = all\n"
            "source_file = config/demo.txt\n"
            "final_file = output/result.txt\n"
            "open_m3u_result = True\n"
            "open_subscribe = True\n"
            "open_history = True\n"
            "open_speed_test = True\n"
            "open_update_time = True\n"
            "request_timeout = 10\n"
            "speed_test_timeout = 10\n"
            "open_empty_category = True\n"
            "app_port = 5180\n"
            "time_zone = Asia/Shanghai\n"
            "language = zh_CN\n"
            "ipv_type_prefer = ipv4,ipv6\n"
            "origin_type_prefer = subscribe,local\n"
        )
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        yield tmp_path
        os.chdir(original_cwd)

    def test_config_loads(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.open_update is True

    def test_urls_limit(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.urls_limit == 15

    def test_min_speed(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.min_speed == 1.0

    def test_min_resolution_value(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.min_resolution_value == 1280 * 720

    def test_ipv_type(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.ipv_type == "all"

    def test_ipv_type_prefer(self, config_with_file):
        mgr = ConfigManager()
        assert "ipv4" in mgr.ipv_type_prefer
        assert "ipv6" in mgr.ipv_type_prefer

    def test_origin_type_prefer(self, config_with_file):
        mgr = ConfigManager()
        assert "subscribe" in mgr.origin_type_prefer
        assert "local" in mgr.origin_type_prefer

    def test_open_ipv6(self, config_with_file):
        mgr = ConfigManager()
        # ipv_type is "all" so open_ipv6 should be True
        assert mgr.open_ipv6 is True

    def test_app_port(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.app_port == 5180

    def test_time_zone(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.time_zone == "Asia/Shanghai"

    def test_language(self, config_with_file):
        mgr = ConfigManager()
        assert mgr.language == "zh_CN"

    def test_env_override(self, config_with_file, monkeypatch):
        monkeypatch.setenv("URLS_LIMIT", "20")
        mgr = ConfigManager()
        assert mgr.urls_limit == 20

    def test_set_method(self, config_with_file):
        mgr = ConfigManager()
        mgr.set("Settings", "urls_limit", "25")
        assert mgr.urls_limit == 25

    def test_save_method(self, config_with_file):
        mgr = ConfigManager()
        mgr.set("Settings", "urls_limit", "30")
        mgr.save()
        # Reload and verify
        mgr2 = ConfigManager()
        assert mgr2.urls_limit == 30

    def test_fallback_values(self, tmp_path):
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "config.ini"
        config_file.write_text("[Settings]\n")
        original_cwd = os.getcwd()
        os.chdir(str(tmp_path))
        try:
            mgr = ConfigManager()
            assert mgr.urls_limit == 10  # default fallback
            assert mgr.min_speed == 0.5  # default fallback
            assert mgr.request_timeout == 10  # default fallback
        finally:
            os.chdir(original_cwd)
