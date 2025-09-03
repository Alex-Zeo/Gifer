import glob
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageOps


def ensure_dir(path: Path) -> None:
    """
    Ensures that a directory exists.
    """
    path.mkdir(parents=True, exist_ok=True)


def list_images(glob_pattern: str, exts: Tuple[str, ...]) -> List[Path]:
    """
    Lists images matching a glob pattern and specific extensions.
    """
    files = glob.glob(glob_pattern, recursive=True)
    return [Path(f) for f in files if f.lower().endswith(exts)]


def exif_autorotate(img: Image.Image) -> Image.Image:
    """
    Applies EXIF orientation to an image.
    """
    return ImageOps.exif_transpose(img)
