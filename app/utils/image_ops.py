from typing import Dict, Literal
from PIL import Image, ImageDraw, ImageFont

# TODO: Add a font file to this path
FONT_PATH = "app/assets/fonts/DejaVuSans.ttf"


def crop_image(img: Image.Image, box: Dict[str, int]) -> Image.Image:
    """
    Crops an image to a specified box.
    Box is a dict with keys "left", "top", "width", "height".
    """
    left = box["left"]
    top = box["top"]
    right = left + box["width"]
    bottom = top + box["height"]
    return img.crop((left, top, right, bottom))


def watermark_text(
    img: Image.Image,
    text: str,
    pos: Literal["top-left", "top-right", "bottom-left", "bottom-right", "center"],
    opacity: float = 0.3,
    font_size: int = 18,
    margin_px: int = 12,
) -> Image.Image:
    """
    Adds a text watermark to an image.
    """
    base = img.convert("RGBA")
    txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(txt_layer)

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x, y = 0, 0
    if pos == "top-left":
        x, y = margin_px, margin_px
    elif pos == "top-right":
        x, y = base.width - text_width - margin_px, margin_px
    elif pos == "bottom-left":
        x, y = margin_px, base.height - text_height - margin_px
    elif pos == "bottom-right":
        x, y = (
            base.width - text_width - margin_px,
            base.height - text_height - margin_px,
        )
    elif pos == "center":
        x, y = (base.width - text_width) / 2, (base.height - text_height) / 2

    fill_opacity = int(255 * opacity)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, fill_opacity))

    return Image.alpha_composite(base, txt_layer).convert("RGB")
