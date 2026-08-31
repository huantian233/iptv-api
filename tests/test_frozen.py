"""Unit tests for utils/frozen.py"""

import gzip
import os
import pickle
import sys
import time
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import frozen
from utils.frozen import (
    mark_url_bad,
    mark_url_good,
    is_url_frozen,
    get_current_frozen_set,
    load,
    save,
    MAX_BACKOFF,
    BASE_BACKOFF,
)


@pytest.fixture(autouse=True)
def clear_frozen_state():
    """Clear the frozen state before each test."""
    frozen._frozen.clear()
    yield
    frozen._frozen.clear()


class TestMarkUrlBad:
    def test_marks_url_as_frozen(self):
        mark_url_bad("http://example.com")
        assert is_url_frozen("http://example.com") is True

    def test_increments_bad_count(self):
        mark_url_bad("http://example.com")
        assert frozen._frozen["http://example.com"]["bad_count"] == 1

    def test_multiple_marks_increase_backoff(self):
        mark_url_bad("http://example.com")
        first_until = frozen._frozen["http://example.com"]["frozen_until"]
        mark_url_bad("http://example.com")
        second_until = frozen._frozen["http://example.com"]["frozen_until"]
        assert second_until > first_until

    def test_empty_url_ignored(self):
        mark_url_bad("")
        assert len(frozen._frozen) == 0

    def test_initial_flag_sets_high_bad_count(self):
        mark_url_bad("http://example.com", initial=True)
        assert frozen._frozen["http://example.com"]["bad_count"] >= 4

    def test_backoff_capped_at_max(self):
        for _ in range(50):
            mark_url_bad("http://example.com")
        meta = frozen._frozen["http://example.com"]
        now = int(time.time())
        assert meta["frozen_until"] - now <= MAX_BACKOFF


class TestMarkUrlGood:
    def test_reduces_bad_count(self):
        mark_url_bad("http://example.com")
        mark_url_bad("http://example.com")
        assert frozen._frozen["http://example.com"]["bad_count"] == 2
        mark_url_good("http://example.com")
        assert frozen._frozen["http://example.com"]["bad_count"] == 1

    def test_removes_entry_when_count_zero(self):
        mark_url_bad("http://example.com")
        mark_url_good("http://example.com")
        assert "http://example.com" not in frozen._frozen

    def test_clears_frozen_until(self):
        mark_url_bad("http://example.com")
        mark_url_good("http://example.com")
        # Entry removed since bad_count reached 0
        assert "http://example.com" not in frozen._frozen

    def test_no_effect_on_unknown_url(self):
        mark_url_good("http://unknown.com")
        assert "http://unknown.com" not in frozen._frozen

    def test_empty_url_ignored(self):
        mark_url_good("")
        assert len(frozen._frozen) == 0


class TestIsUrlFrozen:
    def test_frozen_url(self):
        mark_url_bad("http://example.com")
        assert is_url_frozen("http://example.com") is True

    def test_not_frozen_url(self):
        assert is_url_frozen("http://notfrozen.com") is False

    def test_expired_freeze_returns_false(self):
        mark_url_bad("http://example.com")
        # Manually set frozen_until to the past
        frozen._frozen["http://example.com"]["frozen_until"] = int(time.time()) - 100
        assert is_url_frozen("http://example.com") is False

    def test_expired_freeze_reduces_bad_count(self):
        mark_url_bad("http://example.com")
        mark_url_bad("http://example.com")
        frozen._frozen["http://example.com"]["frozen_until"] = int(time.time()) - 100
        is_url_frozen("http://example.com")
        assert frozen._frozen["http://example.com"]["bad_count"] == 1

    def test_expired_with_zero_count_removes_entry(self):
        mark_url_bad("http://example.com")
        frozen._frozen["http://example.com"]["frozen_until"] = int(time.time()) - 100
        frozen._frozen["http://example.com"]["bad_count"] = 1
        is_url_frozen("http://example.com")
        assert "http://example.com" not in frozen._frozen


class TestGetCurrentFrozenSet:
    def test_returns_frozen_urls(self):
        mark_url_bad("http://a.com")
        mark_url_bad("http://b.com")
        result = get_current_frozen_set()
        assert "http://a.com" in result
        assert "http://b.com" in result

    def test_excludes_expired(self):
        mark_url_bad("http://a.com")
        frozen._frozen["http://a.com"]["frozen_until"] = int(time.time()) - 100
        frozen._frozen["http://a.com"]["bad_count"] = 1
        result = get_current_frozen_set()
        assert "http://a.com" not in result

    def test_empty_state(self):
        result = get_current_frozen_set()
        assert result == set()


class TestLoadAndSave:
    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "frozen.gz")
        mark_url_bad("http://saved.com")
        save(path)
        assert os.path.exists(path)

        frozen._frozen.clear()
        assert "http://saved.com" not in frozen._frozen

        load(path)
        assert "http://saved.com" in frozen._frozen

    def test_load_nonexistent_path(self):
        load("/nonexistent/path.gz")
        assert len(frozen._frozen) == 0

    def test_load_none_path(self):
        load(None)
        assert len(frozen._frozen) == 0

    def test_save_none_path(self):
        save(None)  # Should not raise

    def test_save_creates_directory(self, tmp_path):
        path = str(tmp_path / "subdir" / "frozen.gz")
        mark_url_bad("http://example.com")
        save(path)
        assert os.path.exists(path)

    def test_load_does_not_overwrite_existing(self, tmp_path):
        path = str(tmp_path / "frozen.gz")
        mark_url_bad("http://existing.com")
        save(path)

        frozen._frozen.clear()
        mark_url_bad("http://new.com")
        load(path)

        assert "http://existing.com" in frozen._frozen
        assert "http://new.com" in frozen._frozen

    def test_load_corrupt_file(self, tmp_path):
        path = str(tmp_path / "corrupt.gz")
        with gzip.open(path, "wb") as f:
            f.write(b"not valid pickle data")
        load(path)  # Should not raise
        assert len(frozen._frozen) == 0
