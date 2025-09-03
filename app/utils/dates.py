from datetime import date, timedelta
from typing import List


def inclusive_date_range(start_date: date, end_date: date) -> List[date]:
    """
    Generates a list of dates from start_date to end_date, inclusive.
    """
    if start_date > end_date:
        return []

    delta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


# Note: The 'to_tz' function specified in the plan (def to_tz(d: date, tz: str) -> date)
# is conceptually problematic as Python's 'date' objects are timezone-naive.
# This will be implemented once its usage in 'ensure_date_param' is clearer.
