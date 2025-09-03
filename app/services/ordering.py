import re
from datetime import date
from pathlib import Path
from typing import List, Literal, Optional, Tuple


def detect_date_from_name(name: str) -> Optional[date]:
    """
    Detects a date from a string like 'YYYY-MM-DD.png'.
    """
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def natural_key(s: str) -> Tuple:
    """
    A key for natural sorting (e.g., "file2.txt" before "file10.txt").
    """
    return tuple(int(c) if c.isdigit() else c.lower() for c in re.split("([0-9]+)", s))


def order_images(
    images: List[Path],
    strategy: Literal["auto", "date", "natural", "explicit"],
    explicit: Optional[List[Path]] = None,
) -> List[Path]:
    """
    Orders a list of images based on a specified strategy.
    """
    if strategy == "explicit":
        return explicit or []

    if strategy == "auto":
        # If all images have a date in their name, use date ordering. Otherwise, use natural.
        if all(detect_date_from_name(p.name) for p in images):
            strategy_to_use = "date"
        else:
            strategy_to_use = "natural"
    else:
        strategy_to_use = strategy

    if strategy_to_use == "date":
        return sorted(images, key=lambda p: detect_date_from_name(p.name) or date.min)

    if strategy_to_use == "natural":
        return sorted(images, key=lambda p: natural_key(p.stem))

    return images
