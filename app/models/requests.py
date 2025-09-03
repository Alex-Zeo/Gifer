from datetime import date
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field


class Viewport(BaseModel):
    width: int = 1920
    height: int = 1080
    device_scale_factor: float = 1.0


class RenderWait(BaseModel):
    wait_until: List[str] = ["domcontentloaded", "networkidle"]
    ensure_images_loaded: bool = True
    ensure_fonts_loaded: bool = True
    extra_wait_ms: int = 300
    timeout_ms: int = 30000


class Retries(BaseModel):
    max_attempts: int = 3
    backoff_base_ms: int = 400
    backoff_jitter_ms: int = 200


class Crop(BaseModel):
    selector: Optional[str] = None
    box: Optional[Dict[str, int]] = None


class Watermark(BaseModel):
    text: Optional[str] = None
    position: Literal[
        "top-left", "top-right", "bottom-left", "bottom-right", "center"
    ] = "bottom-right"
    opacity: float = 0.3
    font_size: int = 18
    margin_px: int = 12


class ScreenshotJobRequest(BaseModel):
    url: str
    start_date: date
    end_date: date
    timezone: str = "UTC"
    date_param_name: str = "date"
    date_format: str = "YYYY-MM-DD"
    slug: str
    out_dir: str
    viewport: Viewport = Field(default_factory=Viewport)
    full_page: bool = True
    render_wait: RenderWait = Field(default_factory=RenderWait)
    concurrency: int = 5
    per_host_rate_limit_rps: int = 4
    retries: Retries = Field(default_factory=Retries)
    crop: Optional[Crop] = None
    watermark: Optional[Watermark] = None
    overwrite: bool = False


class DriveUpload(BaseModel):
    enabled: bool = False
    folder_id: Optional[str] = None
    make_anyone_with_link_reader: bool = False


class GifJobRequest(BaseModel):
    images_glob: str
    explicit_images: Optional[List[str]] = None
    order_strategy: Literal["auto", "date", "natural", "explicit"] = "auto"
    output_path: str
    seconds_per_image: float = 0.5
    loop: int = 0
    optimize: bool = True
    transparency: bool = True
    drive_upload: DriveUpload = Field(default_factory=DriveUpload)


class VideoJobRequest(BaseModel):
    images_glob: str
    explicit_images: Optional[List[str]] = None
    order_strategy: Literal["auto", "date", "natural", "explicit"] = "auto"
    output_path: str
    seconds_per_image: float = 0.5
    container: Literal["mp4", "webm"] = "mp4"
    codec: Literal["libx264", "libvpx-vp9", "libaom-av1"] = "libx264"
    crf: int = 18
    preset: str = "medium"
    pix_fmt: str = "yuv420p"
    drive_upload: DriveUpload = Field(default_factory=DriveUpload)
