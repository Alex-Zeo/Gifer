from pathlib import Path
from typing import List
import imageio.v2 as imageio
from PIL import Image
from app.utils.files import exif_autorotate


class GifAgent:
    def build_gif(
        self,
        images: List[Path],
        output_path: Path,
        seconds_per_image: float = 0.5,
        loop: int = 0,
        optimize: bool = True,
    ) -> Path:
        """
        Builds a GIF from a list of images.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        writer = imageio.get_writer(
            output_path,
            mode="I",
            duration=seconds_per_image * 1000,  # imageio expects duration in ms
            loop=loop,
            # optimize=optimize, # Note: optimize is handled differently in imageio v3+
        )

        for image_path in images:
            img = Image.open(image_path)
            rotated_img = exif_autorotate(img)
            writer.append_data(rotated_img)

        writer.close()
        return output_path
