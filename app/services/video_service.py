import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List

from app.logger import get_logger

logger = get_logger(__name__)


class VideoAgent:
    def build_video(
        self,
        images: List[Path],
        output_path: Path,
        seconds_per_image: float = 0.5,
        container: str = "mp4",
        codec: str = "libx264",
        crf: int = 18,
        preset: str = "medium",
        pix_fmt: str = "yuv420p",
    ) -> Path:
        """
        Builds a video from a list of images using FFmpeg.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create sequentially named copies of images
            for i, img_path in enumerate(images):
                link_path = temp_path / f"{i:06d}{img_path.suffix}"
                shutil.copy(img_path, link_path)

            framerate = 1 / seconds_per_image

            command = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-framerate",
                str(framerate),
                "-i",
                str(temp_path / f"%06d{images[0].suffix}"),
                "-c:v",
                codec,
                "-crf",
                str(crf),
                "-preset",
                preset,
                "-pix_fmt",
                pix_fmt,
                str(output_path),
            ]

            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                logger.error(
                    "FFmpeg failed",
                    cmd=" ".join(command),
                    stdout=e.stdout,
                    stderr=e.stderr,
                )
                raise

        return output_path
