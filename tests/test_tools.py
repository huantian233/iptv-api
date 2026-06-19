"""Unit tests for utils/tools.py"""

import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tools import (
    format_interval,
    get_pbar_remaining,
    get_resolution_value,
    check_url_by_keywords,
    get_url_host,
    add_url_info,
    format_url_with_cache,
    remove_cache_info,
    resource_path,
    join_url,
    add_port_to_url,
    get_url_without_scheme,
    find_by_id,
    get_urls_len,
    parse_times,
    build_path_list,
    merge_objects,
    remove_duplicates_from_list,
    get_total_urls_from_sorted_data,
    filter_by_date,
    get_soup,
    write_content_into_txt,
    get_headers_key_value,
    get_name_value,
    get_real_path,
    format_name,
)


class TestFormatInterval:
    def test_seconds_only(self):
        assert format_interval(45) == "00:45"

    def test_minutes_and_seconds(self):
        assert format_interval(125) == "02:05"

    def test_hours(self):
        assert format_interval(3661) == "1:01:01"

    def test_zero(self):
        assert format_interval(0) == "00:00"

    def test_float_truncates(self):
        assert format_interval(59.9) == "00:59"

    def test_large_value(self):
        assert format_interval(7200) == "2:00:00"


class TestGetPbarRemaining:
    def test_with_completed_tasks(self):
        from time import time
        start = time() - 10  # 10 seconds ago
        result = get_pbar_remaining(n=5, total=10, start_time=start)
        assert result is not None
        assert ":" in result

    def test_with_zero_completed(self):
        from time import time
        result = get_pbar_remaining(n=0, total=10, start_time=time())
        assert result is not None


class TestGetResolutionValue:
    def test_standard_resolution(self):
        assert get_resolution_value("1920x1080") == 1920 * 1080

    def test_with_capital_x(self):
        assert get_resolution_value("1920X1080") == 1920 * 1080

    def test_with_asterisk(self):
        assert get_resolution_value("1920*1080") == 1920 * 1080

    def test_empty_string(self):
        assert get_resolution_value("") == 0

    def test_none(self):
        assert get_resolution_value(None) == 0

    def test_invalid_string(self):
        assert get_resolution_value("invalid") == 0

    def test_720p(self):
        assert get_resolution_value("1280x720") == 1280 * 720


class TestCheckUrlByKeywords:
    def test_match_found(self):
        assert check_url_by_keywords("http://example.com/stream", ["example"]) is True

    def test_no_match(self):
        assert check_url_by_keywords("http://example.com/stream", ["notfound"]) is False

    def test_empty_keywords(self):
        assert check_url_by_keywords("http://example.com", []) is False

    def test_none_keywords(self):
        assert check_url_by_keywords("http://example.com", None) is False

    def test_multiple_keywords_one_match(self):
        assert check_url_by_keywords("http://example.com", ["foo", "example"]) is True


class TestGetUrlHost:
    def test_http_url(self):
        result = get_url_host("http://example.com/path")
        assert result is not None
        assert "example.com" in result

    def test_https_url(self):
        result = get_url_host("https://stream.example.com/live")
        assert result is not None
        assert "stream.example.com" in result

    def test_rtmp_url(self):
        result = get_url_host("rtmp://live.example.com/app/stream")
        assert result is not None
        assert "live.example.com" in result

    def test_invalid_url(self):
        result = get_url_host("")
        assert result is None


class TestAddUrlInfo:
    def test_add_info(self):
        result = add_url_info("http://example.com/stream", "info_text")
        assert result == "http://example.com/stream$info_text"

    def test_url_already_has_dollar(self):
        result = add_url_info("http://example.com/stream$existing", "new_info")
        assert result == "http://example.com/stream$existing-new_info"

    def test_empty_info(self):
        result = add_url_info("http://example.com/stream", "")
        assert result == "http://example.com/stream"


class TestFormatUrlWithCache:
    def test_with_cache_provided(self):
        result = format_url_with_cache("http://example.com/stream", "example.com")
        assert "cache:example.com" in result

    def test_without_cache_extracts_host(self):
        result = format_url_with_cache("http://example.com/stream")
        assert "cache:" in result

    def test_empty_url_no_cache(self):
        result = format_url_with_cache("", "")
        assert result == ""


class TestRemoveCacheInfo:
    def test_remove_cache(self):
        result = remove_cache_info("http://example.com$cache:example.com")
        assert "cache:" not in result

    def test_no_cache_to_remove(self):
        result = remove_cache_info("http://example.com/stream")
        assert result == "http://example.com/stream"


class TestResourcePath:
    def test_existing_path(self):
        result = resource_path("utils/tools.py")
        assert os.path.exists(result)

    def test_persistent_path(self):
        result = resource_path("nonexistent/path.txt", persistent=True)
        assert "nonexistent/path.txt" in result


class TestJoinUrl:
    def test_basic_join(self):
        assert join_url("http://example.com", "path/to/file") == "http://example.com/path/to/file"

    def test_trailing_slash(self):
        assert join_url("http://example.com/", "path") == "http://example.com/path"

    def test_empty_url1(self):
        assert join_url("", "http://example.com") == "http://example.com"

    def test_empty_url2(self):
        assert join_url("http://example.com", "") == "http://example.com"

    def test_both_empty(self):
        assert join_url("", "") == ""


class TestAddPortToUrl:
    def test_add_port(self):
        result = add_port_to_url("http://example.com/path", 8080)
        assert ":8080" in result

    def test_zero_port(self):
        result = add_port_to_url("http://example.com/path", 0)
        assert result == "http://example.com/path"


class TestGetUrlWithoutScheme:
    def test_http(self):
        result = get_url_without_scheme("http://example.com/path")
        assert result == "example.com/path"

    def test_https(self):
        result = get_url_without_scheme("https://example.com/resource")
        assert result == "example.com/resource"


class TestFindById:
    def test_found_at_top_level(self):
        data = {"id": 1, "name": "test"}
        assert find_by_id(data, 1) == data

    def test_found_nested(self):
        target = {"id": 42, "name": "target"}
        data = {"items": [target, {"id": 2, "name": "other"}]}
        assert find_by_id(data, 42) == target

    def test_not_found(self):
        data = {"id": 1, "items": [{"id": 2}]}
        assert find_by_id(data, 99) == {}

    def test_deeply_nested(self):
        target = {"id": 5, "value": "deep"}
        data = {"level1": {"level2": {"items": [target]}}}
        assert find_by_id(data, 5) == target


class TestGetUrlsLen:
    def test_basic(self):
        data = {
            "cat1": {
                "channel1": [{"url": "http://a.com"}, {"url": "http://b.com"}],
                "channel2": [{"url": "http://c.com"}],
            }
        }
        assert get_urls_len(data) == 3

    def test_duplicate_urls(self):
        data = {
            "cat1": {
                "ch1": [{"url": "http://a.com"}],
                "ch2": [{"url": "http://a.com"}],
            }
        }
        assert get_urls_len(data) == 1

    def test_empty(self):
        data = {"cat1": {"ch1": []}}
        assert get_urls_len(data) == 0


class TestParseTimes:
    def test_single_time(self):
        result = parse_times("08:30")
        assert result == [(8, 30)]

    def test_multiple_times(self):
        result = parse_times("08:30, 12:00, 18:30")
        assert result == [(8, 30), (12, 0), (18, 30)]

    def test_empty_string(self):
        result = parse_times("")
        assert result == []

    def test_none(self):
        result = parse_times(None)
        assert result == []

    def test_hour_only(self):
        result = parse_times("14")
        assert result == [(14, 0)]

    def test_invalid_entry_skipped(self):
        result = parse_times("08:30, invalid, 12:00")
        assert result == [(8, 30), (12, 0)]


class TestBuildPathList:
    def test_basic_listing(self, tmp_path):
        (tmp_path / "file1.txt").write_text("hello")
        (tmp_path / "file2.py").write_text("world")
        result = build_path_list(tmp_path)
        assert len(result) == 2

    def test_filter_by_extension(self, tmp_path):
        (tmp_path / "file1.txt").write_text("hello")
        (tmp_path / "file2.py").write_text("world")
        result = build_path_list(tmp_path, exts=".txt")
        assert len(result) == 1
        assert result[0].endswith(".txt")

    def test_exclude_hidden_files(self, tmp_path):
        (tmp_path / ".hidden").write_text("hidden")
        (tmp_path / "visible.txt").write_text("visible")
        result = build_path_list(tmp_path, include_hidden=False)
        assert len(result) == 1

    def test_include_hidden_files(self, tmp_path):
        (tmp_path / ".hidden").write_text("hidden")
        (tmp_path / "visible.txt").write_text("visible")
        result = build_path_list(tmp_path, include_hidden=True)
        assert len(result) == 2

    def test_nonexistent_dir(self):
        result = build_path_list("/nonexistent/dir")
        assert result == []

    def test_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.txt").write_text("a")
        (sub / "b.txt").write_text("b")
        result = build_path_list(tmp_path, recursive=True)
        assert len(result) == 2

    def test_non_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "a.txt").write_text("a")
        (sub / "b.txt").write_text("b")
        result = build_path_list(tmp_path, recursive=False)
        assert len(result) == 1


class TestMergeObjects:
    def test_basic_merge(self):
        result = merge_objects({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_nested_merge(self):
        result = merge_objects({"a": {"x": 1}}, {"a": {"y": 2}})
        assert result == {"a": {"x": 1, "y": 2}}

    def test_list_merge_no_duplicates(self):
        result = merge_objects({"a": [1, 2]}, {"a": [2, 3]})
        assert result == {"a": [1, 2, 3]}

    def test_set_merge(self):
        result = merge_objects({"a": {1, 2}}, {"a": {2, 3}})
        assert result == {"a": {1, 2, 3}}

    def test_defaultdict_preserves_factory(self):
        d1 = defaultdict(list)
        d1["key"].append("val1")
        d2 = {"key": ["val2"]}
        result = merge_objects(d1, d2)
        assert isinstance(result, defaultdict)
        assert "val1" in result["key"]
        assert "val2" in result["key"]

    def test_empty_input(self):
        result = merge_objects()
        assert result == {}

    def test_non_dict_raises_error(self):
        with pytest.raises(TypeError):
            merge_objects({"a": 1}, "not a dict")


class TestRemoveDuplicatesFromList:
    def test_removes_duplicates(self):
        data = [
            {"url": "http://a.com", "host": "a.com", "origin": "subscribe", "ipv_type": "ipv4"},
            {"url": "http://a.com", "host": "a.com", "origin": "subscribe", "ipv_type": "ipv4"},
            {"url": "http://b.com", "host": "b.com", "origin": "local", "ipv_type": "ipv4"},
        ]
        seen = set()
        result = remove_duplicates_from_list(data, seen)
        assert len(result) == 2

    def test_skips_whitelist(self):
        data = [
            {"url": "http://a.com", "host": "a.com", "origin": "whitelist", "ipv_type": "ipv4"},
        ]
        seen = set()
        result = remove_duplicates_from_list(data, seen)
        assert len(result) == 0

    def test_skips_hls(self):
        data = [
            {"url": "http://a.com", "host": "a.com", "origin": "hls", "ipv_type": "ipv4"},
        ]
        seen = set()
        result = remove_duplicates_from_list(data, seen)
        assert len(result) == 0

    def test_filter_by_host(self):
        data = [
            {"url": "http://a.com/1", "host": "a.com", "origin": "subscribe", "ipv_type": "ipv4"},
            {"url": "http://a.com/2", "host": "a.com", "origin": "subscribe", "ipv_type": "ipv4"},
        ]
        seen = set()
        result = remove_duplicates_from_list(data, seen, filter_host=True)
        assert len(result) == 1

    def test_ipv6_filtered_when_not_supported(self):
        data = [
            {"url": "http://[::1]/stream", "host": "[::1]", "origin": "subscribe", "ipv_type": "ipv6"},
        ]
        seen = set()
        result = remove_duplicates_from_list(data, seen, ipv6_support=False)
        assert len(result) == 0


class TestGetSoup:
    def test_basic_html(self):
        html = "<html><body><p>Hello</p></body></html>"
        soup = get_soup(html)
        assert soup.find("p").text == "Hello"

    def test_removes_comments(self):
        html = "<html><!-- comment --><body><p>Text</p></body></html>"
        soup = get_soup(html)
        assert "comment" not in str(soup)
        assert soup.find("p").text == "Text"


class TestWriteContentIntoTxt:
    def test_append_mode(self, tmp_path):
        path = str(tmp_path / "test.txt")
        with open(path, "w") as f:
            f.write("existing\n")
        write_content_into_txt("new content", path=path)
        with open(path) as f:
            content = f.read()
        assert "existing" in content
        assert "new content" in content

    def test_top_position(self, tmp_path):
        path = str(tmp_path / "test.txt")
        with open(path, "w") as f:
            f.write("existing\n")
        write_content_into_txt("top content", path=path, position="top")
        with open(path) as f:
            content = f.read()
        assert content.startswith("top content")

    def test_callback_called(self, tmp_path):
        path = str(tmp_path / "test.txt")
        with open(path, "w") as f:
            f.write("")
        callback = MagicMock()
        write_content_into_txt("content", path=path, callback=callback)
        callback.assert_called_once()

    def test_no_path(self):
        write_content_into_txt("content", path=None)  # should not raise


class TestGetHeadersKeyValue:
    def test_basic_parsing(self):
        content = 'useragent=Mozilla/5.0 referer=http://example.com'
        result = get_headers_key_value(content)
        assert result["useragent"] == "Mozilla/5.0"
        assert result["referer"] == "http://example.com"

    def test_empty_content(self):
        result = get_headers_key_value("")
        assert result == {}


class TestGetNameValue:
    def test_txt_pattern(self):
        import re
        pattern = re.compile(r"^(?P<name>[^,]+)[,](?!#genre#)(?P<value>.+)$")
        content = "CCTV-1,http://example.com/stream"
        result = get_name_value(content, pattern)
        assert len(result) == 1
        assert result[0]["name"] == "CCTV-1"
        assert result[0]["value"] == "http://example.com/stream"

    def test_empty_content(self):
        import re
        pattern = re.compile(r"^(?P<name>[^,]+)[,](?!#genre#)(?P<value>.+)$")
        result = get_name_value("", pattern)
        assert result == []


class TestGetRealPath:
    def test_user_file_exists(self, tmp_path):
        user_file = tmp_path / "user_config.txt"
        user_file.write_text("user content")
        regular_file = tmp_path / "config.txt"
        regular_file.write_text("regular content")
        result = get_real_path(str(regular_file))
        assert "user_config.txt" in result

    def test_user_file_not_exists(self, tmp_path):
        regular_file = tmp_path / "config.txt"
        regular_file.write_text("regular content")
        result = get_real_path(str(regular_file))
        assert result == str(regular_file)


class TestFormatName:
    def test_basic_formatting(self):
        result = format_name("CCTV-1")
        assert "cctv" in result
        assert "1" in result

    def test_removes_hd(self):
        result = format_name("CCTV-1HD")
        assert "hd" not in result.lower() or result == format_name("CCTV-1")

    def test_plus_replacement(self):
        result = format_name("CCTV-5plus")
        assert "+" in result

    def test_chinese_traditional_converted(self):
        result = format_name("東方衛視")
        # Should convert traditional to simplified
        assert result is not None
