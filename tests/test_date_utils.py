from datetime import date
import pytest
from app.utils.dates import inclusive_date_range


@pytest.mark.parametrize(
    "start, end, expected_len",
    [
        (date(2025, 1, 1), date(2025, 1, 5), 5),
        (date(2025, 1, 1), date(2025, 1, 1), 1),
        (date(2025, 1, 5), date(2025, 1, 1), 0),
    ],
)
def test_inclusive_date_range(start, end, expected_len):
    result = inclusive_date_range(start, end)
    assert len(result) == expected_len
    if expected_len > 0:
        assert result[0] == start
        assert result[-1] == end
