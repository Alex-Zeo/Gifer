from datetime import date
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode


def with_query_param(url: str, key: str, value: str) -> str:
    """
    Adds or replaces a query parameter in a URL.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params[key] = [value]
    new_query = urlencode(query_params, doseq=True)

    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment,
        )
    )


def _translate_date_format(format_str: str) -> str:
    """
    Translates a common, non-Python date format string to a strftime-compatible format.
    Example: "YYYY-MM-DD" -> "%Y-%m-%d"
    """
    return format_str.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")


def ensure_date_param(
    url: str, date_param_name: str, dt: date, fmt: str, tz: str
) -> str:
    """
    Ensures a URL has a specific date query parameter.
    'tz' is noted but not used, as 'date' objects are timezone-naive.
    """
    python_fmt = _translate_date_format(fmt)
    date_str = dt.strftime(python_fmt)
    return with_query_param(url, date_param_name, date_str)
