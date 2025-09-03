#!/usr/bin/env python3
"""
Script to create GIFs from scraped screenshots.
"""

import argparse
from pathlib import Path
from typing import Optional
import sys

# Add app to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from app.models.requests import GifJobRequest, DriveUpload
from app.services.gif_service import GifAgent
from app.services.ordering import order_images
from app.services.drive_service import GoogleDriveUploader
from app.utils.files import list_images
from app.logger import get_logger
from app.config import settings

logger = get_logger(__name__)

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".bmp")


def create_gif_from_directory(
    input_dir: str,
    output_path: str,
    seconds_per_image: float = 0.5,
    loop: bool = True,
    optimize: bool = True,
    order_strategy: str = "date",
    upload_to_drive: bool = False,
    drive_folder_id: Optional[str] = None,
    make_public: bool = False
) -> str:
    """Create a GIF from images in a directory."""
    
    # Find all images in the directory
    images_glob = f"{input_dir}/*"
    source_images = list_images(images_glob, IMAGE_EXTENSIONS)
    
    if not source_images:
        raise ValueError(f"No images found in directory: {input_dir}")
    
    logger.info(f"Found {len(source_images)} images in {input_dir}")
    
    # Order the images
    ordered = order_images(source_images, order_strategy)
    
    # Create GIF
    agent = GifAgent()
    gif_path = agent.build_gif(
        ordered,
        Path(output_path),
        seconds_per_image,
        loop,
        optimize,
    )
    
    logger.info(f"GIF created: {gif_path}")
    
    # Upload to Google Drive if requested
    drive_file_id = None
    if upload_to_drive:
        uploader = GoogleDriveUploader()
        drive_file_id = uploader.upload(
            gif_path,
            drive_folder_id or settings.GOOGLE_DRIVE_DEFAULT_FOLDER_ID,
            make_public or settings.GOOGLE_DRIVE_SHARE_ANYONE,
        )
        if drive_file_id:
            logger.info(f"GIF uploaded to Google Drive: {drive_file_id}")
    
    return str(gif_path)


def main():
    parser = argparse.ArgumentParser(description="Create GIF from screenshot images")
    parser.add_argument("--input-dir", required=True, help="Directory containing images")
    parser.add_argument("--output-path", required=True, help="Output GIF path")
    parser.add_argument("--seconds-per-image", type=float, default=0.5, help="Seconds per image in GIF")
    parser.add_argument("--no-loop", action="store_true", help="Don't loop the GIF")
    parser.add_argument("--no-optimize", action="store_true", help="Don't optimize the GIF")
    parser.add_argument("--order-strategy", default="date", choices=["auto", "date", "natural", "explicit"], help="Image ordering strategy")
    parser.add_argument("--upload-to-drive", action="store_true", help="Upload to Google Drive")
    parser.add_argument("--drive-folder-id", help="Google Drive folder ID")
    parser.add_argument("--make-public", action="store_true", help="Make Google Drive file public")
    
    args = parser.parse_args()
    
    try:
        gif_path = create_gif_from_directory(
            input_dir=args.input_dir,
            output_path=args.output_path,
            seconds_per_image=args.seconds_per_image,
            loop=not args.no_loop,
            optimize=not args.no_optimize,
            order_strategy=args.order_strategy,
            upload_to_drive=args.upload_to_drive,
            drive_folder_id=args.drive_folder_id,
            make_public=args.make_public
        )
        
        print(f"SUCCESS: GIF created at {gif_path}")
        
    except Exception as e:
        logger.error(f"Failed to create GIF: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
