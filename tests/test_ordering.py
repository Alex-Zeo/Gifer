from pathlib import Path
import pytest
from app.services.ordering import order_images


@pytest.fixture
def image_files():
    return [
        Path("2025-01-01.png"),
        Path("2025-01-10.png"),
        Path("2025-01-02.png"),
    ]


@pytest.fixture
def natural_files():
    return [Path("img1.png"), Path("img10.png"), Path("img2.png")]


def test_order_by_date(image_files):
    ordered = order_images(image_files, "date")
    assert [p.name for p in ordered] == [
        "2025-01-01.png",
        "2025-01-02.png",
        "2025-01-10.png",
    ]


def test_order_by_natural(natural_files):
    ordered = order_images(natural_files, "natural")
    assert [p.name for p in ordered] == ["img1.png", "img2.png", "img10.png"]


def test_order_auto_detects_date(image_files):
    ordered = order_images(image_files, "auto")
    assert [p.name for p in ordered] == [
        "2025-01-01.png",
        "2025-01-02.png",
        "2025-01-10.png",
    ]


def test_order_auto_falls_back_to_natural(natural_files):
    ordered = order_images(natural_files, "auto")
    assert [p.name for p in ordered] == ["img1.png", "img2.png", "img10.png"]


def test_order_explicit():
    files = [Path("a.png"), Path("b.png"), Path("c.png")]
    explicit_order = [Path("c.png"), Path("a.png"), Path("b.png")]
    ordered = order_images(files, "explicit", explicit=explicit_order)
    assert ordered == explicit_order
