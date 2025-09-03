from datetime import date
import pytest
from app.utils.url import with_query_param, ensure_date_param


@pytest.mark.parametrize(
    "url, key, value, expected",
    [
        ("http://test.com", "a", "b", "http://test.com?a=b"),
        ("http://test.com?a=1", "a", "b", "http://test.com?a=b"),
        ("http://test.com?a=1", "c", "d", "http://test.com?a=1&c=d"),
    ],
)
def test_with_query_param(url, key, value, expected):
    assert with_query_param(url, key, value) == expected


def test_ensure_date_param():
    url = "http://test.com"
    dt = date(2025, 8, 1)
    new_url = ensure_date_param(url, "d", dt, "YYYY-MM-DD", "UTC")
    assert new_url == "http://test.com?d=2025-08-01"
