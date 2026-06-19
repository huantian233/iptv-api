"""Unit tests for utils/whitelist.py"""

import os
import sys
from collections import defaultdict
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.whitelist import (
    is_url_whitelisted,
    get_whitelist_url,
    get_whitelist_total_count,
    load_whitelist_maps,
    get_section_entries,
)


class TestIsUrlWhitelisted:
    def test_exact_match_channel_specific(self):
        exact = defaultdict(list, {"CCTV-1": ["http://exact.com/stream"]})
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        assert is_url_whitelisted(data_map, "http://exact.com/stream", "CCTV-1") is True

    def test_exact_match_global(self):
        exact = defaultdict(list, {"": ["http://global.com/stream"]})
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        assert is_url_whitelisted(data_map, "http://global.com/stream") is True

    def test_keyword_match_channel_specific(self):
        exact = defaultdict(list)
        keywords = defaultdict(list, {"CCTV-1": ["keyword"]})
        data_map = (exact, keywords)
        assert is_url_whitelisted(data_map, "http://example.com/keyword/stream", "CCTV-1") is True

    def test_keyword_match_global(self):
        exact = defaultdict(list)
        keywords = defaultdict(list, {"": ["global_kw"]})
        data_map = (exact, keywords)
        assert is_url_whitelisted(data_map, "http://example.com/global_kw/path") is True

    def test_no_match(self):
        exact = defaultdict(list, {"CCTV-1": ["http://other.com"]})
        keywords = defaultdict(list, {"CCTV-1": ["nothere"]})
        data_map = (exact, keywords)
        assert is_url_whitelisted(data_map, "http://example.com/stream", "CCTV-1") is False

    def test_empty_url(self):
        exact = defaultdict(list, {"": ["http://any.com"]})
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        assert is_url_whitelisted(data_map, "", "channel") is False

    def test_none_data_map(self):
        assert is_url_whitelisted(None, "http://example.com") is False

    def test_empty_data_map(self):
        data_map = (defaultdict(list), defaultdict(list))
        assert is_url_whitelisted(data_map, "http://example.com") is False


class TestGetWhitelistUrl:
    def test_channel_specific_urls(self):
        exact = defaultdict(list, {"CCTV-1": ["http://a.com", "http://b.com"]})
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        result = get_whitelist_url(data_map, "CCTV-1")
        assert "http://a.com" in result
        assert "http://b.com" in result

    def test_global_urls_included(self):
        exact = defaultdict(list, {"": ["http://global.com"], "CCTV-1": ["http://channel.com"]})
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        result = get_whitelist_url(data_map, "CCTV-1")
        assert "http://global.com" in result
        assert "http://channel.com" in result

    def test_no_urls_for_channel(self):
        exact = defaultdict(list, {"CCTV-2": ["http://a.com"]})
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        result = get_whitelist_url(data_map, "CCTV-1")
        assert "http://a.com" not in result or len(result) == 0

    def test_none_channel(self):
        exact = defaultdict(list, {"": ["http://global.com"]})
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        result = get_whitelist_url(data_map, None)
        assert "http://global.com" in result


class TestGetWhitelistTotalCount:
    def test_counts_unique_entries(self):
        exact = defaultdict(list, {
            "ch1": ["http://a.com", "http://b.com"],
            "ch2": ["http://c.com"],
        })
        keywords = defaultdict(list, {
            "": ["keyword1"],
        })
        data_map = (exact, keywords)
        assert get_whitelist_total_count(data_map) == 4

    def test_deduplicates(self):
        exact = defaultdict(list, {
            "ch1": ["http://a.com"],
            "ch2": ["http://a.com"],
        })
        keywords = defaultdict(list)
        data_map = (exact, keywords)
        assert get_whitelist_total_count(data_map) == 1

    def test_empty_maps(self):
        data_map = (defaultdict(list), defaultdict(list))
        assert get_whitelist_total_count(data_map) == 0


class TestLoadWhitelistMaps:
    def test_load_basic_file(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text(
            "CCTV-1,http://stream1.com\n"
            "CCTV-2,http://stream2.com\n"
            "http://global.com\n"
        )
        with patch("utils.whitelist.get_real_path", return_value=str(whitelist_file)):
            with patch("utils.whitelist.resource_path", return_value=str(whitelist_file)):
                exact, keywords = load_whitelist_maps(str(whitelist_file))
        assert "http://stream1.com" in exact["CCTV-1"]
        assert "http://stream2.com" in exact["CCTV-2"]
        assert "http://global.com" in exact[""]

    def test_load_with_keywords_section(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text(
            "CCTV-1,http://exact.com\n"
            "[KEYWORDS]\n"
            "CCTV-1,keyword1\n"
            "keyword2\n"
        )
        with patch("utils.whitelist.get_real_path", return_value=str(whitelist_file)):
            with patch("utils.whitelist.resource_path", return_value=str(whitelist_file)):
                exact, keywords = load_whitelist_maps(str(whitelist_file))
        assert "http://exact.com" in exact["CCTV-1"]
        assert "keyword1" in keywords["CCTV-1"]
        assert "keyword2" in keywords[""]

    def test_load_nonexistent_file(self, tmp_path):
        with patch("utils.whitelist.get_real_path", return_value=str(tmp_path / "nonexistent.txt")):
            with patch("utils.whitelist.resource_path", return_value=str(tmp_path / "nonexistent.txt")):
                exact, keywords = load_whitelist_maps(str(tmp_path / "nonexistent.txt"))
        assert len(exact) == 0
        assert len(keywords) == 0

    def test_comments_and_empty_lines_skipped(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text(
            "# This is a comment\n"
            "\n"
            "CCTV-1,http://stream1.com\n"
            "# Another comment\n"
        )
        with patch("utils.whitelist.get_real_path", return_value=str(whitelist_file)):
            with patch("utils.whitelist.resource_path", return_value=str(whitelist_file)):
                exact, keywords = load_whitelist_maps(str(whitelist_file))
        assert "http://stream1.com" in exact["CCTV-1"]
        assert len(exact) == 1

    def test_no_duplicate_entries(self, tmp_path):
        whitelist_file = tmp_path / "whitelist.txt"
        whitelist_file.write_text(
            "CCTV-1,http://stream1.com\n"
            "CCTV-1,http://stream1.com\n"
        )
        with patch("utils.whitelist.get_real_path", return_value=str(whitelist_file)):
            with patch("utils.whitelist.resource_path", return_value=str(whitelist_file)):
                exact, keywords = load_whitelist_maps(str(whitelist_file))
        assert exact["CCTV-1"].count("http://stream1.com") == 1


class TestGetSectionEntries:
    def test_basic_section_parsing(self, tmp_path):
        file_path = tmp_path / "whitelist.txt"
        file_path.write_text(
            "[WHITELIST]\n"
            "http://inside.com\n"
            "[OTHER]\n"
            "http://outside.com\n"
        )
        with patch("utils.whitelist.get_real_path", return_value=str(file_path)):
            with patch("utils.whitelist.resource_path", return_value=str(file_path)):
                inside, outside = get_section_entries(str(file_path), "WHITELIST")
        assert "http://inside.com" in inside
        assert "http://outside.com" in outside

    def test_nonexistent_file(self, tmp_path):
        with patch("utils.whitelist.get_real_path", return_value=str(tmp_path / "nope.txt")):
            with patch("utils.whitelist.resource_path", return_value=str(tmp_path / "nope.txt")):
                inside, outside = get_section_entries(str(tmp_path / "nope.txt"))
        assert inside == []
        assert outside == []
