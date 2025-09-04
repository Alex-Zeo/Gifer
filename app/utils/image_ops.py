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
    opacity: float = 0.4,  # Reduced opacity for centered watermarks
    font_size: int = None, # Dynamic sizing based on image dimensions
    margin_px: int = 20,   # Larger margin for centered placement
    stroke_width: int = 2, # 2px stroke for contrast
    stroke_color: tuple = (0, 0, 0),  # Black stroke
    scale_factor: float = 0.08,  # Font size as fraction of image width (8%)
) -> Image.Image:
    """
    Adds a text watermark to an image with dynamic sizing and optimal placement.
    
    Args:
        img: Source image
        text: Watermark text
        pos: Position (defaults to center for best visibility)
        opacity: Text opacity (0.0-1.0, default 0.4 for subtle centered watermarks)
        font_size: Fixed font size (if None, calculates dynamically)
        margin_px: Margin from edges
        stroke_width: Outline stroke width for contrast
        stroke_color: Outline color
        scale_factor: Font size as fraction of image width (used when font_size=None)
    """
    base = img.convert("RGBA")
    txt_layer = Image.new("RGBA", base.size, (255, 255, 255, 0))

    # Calculate dynamic font size if not specified
    if font_size is None:
        # Target font size as percentage of image width for optimal scaling
        # This ensures watermark is appropriately sized for any resolution
        target_width = base.width * scale_factor
        # Start with a reasonable base size and scale up/down
        font_size = max(12, int(target_width / len(text) * 2.5))
        # Cap at reasonable bounds
        font_size = min(font_size, base.height // 8)  # Not larger than 1/8 image height
        font_size = max(font_size, 16)  # Minimum readable size

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(txt_layer)

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Calculate position with improved centering and margins
    if pos == "center":
        # Perfect center with slight bias to avoid critical map elements
        x = (base.width - text_width) / 2
        y = (base.height - text_height) / 2
        # Add subtle offset if needed to avoid covering central features
        # For maps, slightly lower is often better than dead center
        y += text_height * 0.1  # Slight downward bias
    elif pos == "top-left":
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
    else:
        # Default to center if position not recognized
        x, y = (base.width - text_width) / 2, (base.height - text_height) / 2

    fill_opacity = int(255 * opacity)
    
    # Draw stroke/outline if requested
    if stroke_width > 0:
        stroke_opacity = int(255 * opacity)  # Same opacity for stroke
        stroke_fill = (*stroke_color, stroke_opacity)
        
        # Draw stroke by drawing text slightly offset in all directions
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx != 0 or dy != 0:  # Don't draw at center position yet
                    draw.text((x + dx, y + dy), text, font=font, fill=stroke_fill)
    
    # Draw the main text on top
    draw.text((x, y), text, font=font, fill=(255, 255, 255, fill_opacity))

    return Image.alpha_composite(base, txt_layer).convert("RGB")
