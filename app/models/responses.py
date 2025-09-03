from typing import List, Optional
from pydantic import BaseModel


class ScreenshotJobResponse(BaseModel):
    job_id: str
    saved_count: int
    skipped_existing: int
    failures: List[str]
    out_dir: str
    files: List[str]


class ConvertGifResponse(BaseModel):
    frames: int
    duration_s: float
    gif_path: str
    drive_file_id: Optional[str] = None
    warnings: List[str] = []


class ConvertVideoResponse(BaseModel):
    frames: int
    duration_s: float
    video_path: str
    drive_file_id: Optional[str] = None
    warnings: List[str] = []
