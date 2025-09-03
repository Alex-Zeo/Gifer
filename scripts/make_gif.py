#!/usr/bin/env python3
"""
Script to create GIFs from scraped screenshots.
"""

import argparse
from pathlib import Path
from typing import Optional
import sys
from PIL import Image

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
    loop: int = 0,  # 0 = infinite loop (default)
    optimize: bool = True,
    order_strategy: str = "date",
    upload_to_drive: bool = False,
    drive_folder_id: Optional[str] = None,
    make_public: bool = False,
    watermark_prefix: Optional[str] = None,
    watermark_position: str = "top-left"  # Updated default to top-left
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
    
    # Add watermarks if requested
    final_images = ordered
    if watermark_prefix:
        import tempfile
        import shutil
        from datetime import datetime
        from app.utils.image_ops import watermark_text
        
        # Create temporary directory for watermarked images
        temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"Creating watermarked images in {temp_dir}")
        
        watermarked_images = []
        for img_path in ordered:
            # Extract date from filename (assuming format like "2025-08-01.png")
            stem = img_path.stem
            try:
                # Parse date from filename (e.g., "2025-08-01" -> "GPSJAM 08-01-25")
                date_obj = datetime.strptime(stem, "%Y-%m-%d")
                short_date = date_obj.strftime("%m-%d-%y")  # Format as MM-DD-YY
                watermark_text_str = f"{watermark_prefix} {short_date}"
                logger.debug(f"Processing {stem} -> watermark: '{watermark_text_str}'")
            except ValueError:
                # Fallback if date parsing fails
                watermark_text_str = f"{watermark_prefix} {stem}"
                logger.warning(f"Could not parse date from filename: {stem}, using fallback")
            
            # Load image and add watermark with large font and stroke (new defaults)
            img = Image.open(img_path)
            watermarked_img = watermark_text(
                img, 
                watermark_text_str, 
                watermark_position,
                opacity=0.8,  # 80% opacity
                font_size=60,  # 60 point font (default for high visibility)
                margin_px=15,
                stroke_width=2,  # 2px black stroke (default for contrast)
                stroke_color=(0, 0, 0)  # Black stroke
            )
            
            # Save watermarked image to temp directory
            temp_img_path = temp_dir / img_path.name
            watermarked_img.save(temp_img_path)
            watermarked_images.append(temp_img_path)
        
        final_images = watermarked_images
        logger.info(f"Added watermarks to {len(watermarked_images)} images")
    
    # Create GIF
    agent = GifAgent()
    gif_path = agent.build_gif(
        final_images,
        Path(output_path),
        seconds_per_image,
        loop,
        optimize,
    )
    
    # Clean up temporary directory if watermarks were used
    if watermark_prefix and 'temp_dir' in locals():
        shutil.rmtree(temp_dir)
        logger.info("Cleaned up temporary watermarked images")
    
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
    parser.add_argument("--loop-count", type=int, default=0, help="Number of loops (0 = infinite, default)")
    parser.add_argument("--no-optimize", action="store_true", help="Don't optimize the GIF")
    parser.add_argument("--order-strategy", default="date", choices=["auto", "date", "natural", "explicit"], help="Image ordering strategy")
    parser.add_argument("--upload-to-drive", action="store_true", help="Upload to Google Drive")
    parser.add_argument("--drive-folder-id", help="Google Drive folder ID")
    parser.add_argument("--make-public", action="store_true", help="Make Google Drive file public")
    parser.add_argument("--watermark-prefix", help="Add watermark prefix (e.g., 'GPSJAM' will add 'GPSJAM MM/DD' to each image)")
    parser.add_argument("--watermark-position", default="top-left", choices=["top-left", "top-right", "bottom-left", "bottom-right", "center"], help="Watermark position")
    
    # Compression options
    parser.add_argument("--compress", action="store_true", help="Compress GIF to stay under size limit")
    parser.add_argument("--max-size-mb", type=float, default=14.99, help="Maximum GIF size in MB (default: 14.99)")
    parser.add_argument("--rename-output", help="Rename output file (without .gif extension)")
    
    args = parser.parse_args()
    
    try:
            gif_path = create_gif_from_directory(
            input_dir=args.input_dir,
            output_path=args.output_path,
            seconds_per_image=args.seconds_per_image,
            loop=args.loop_count,
            optimize=not args.no_optimize,
            order_strategy=args.order_strategy,
            upload_to_drive=args.upload_to_drive,
            drive_folder_id=args.drive_folder_id,
            make_public=args.make_public,
            watermark_prefix=args.watermark_prefix,
            watermark_position=args.watermark_position
        )
        
        # Optional compression
        if args.compress:
            from app.services.compression_service import CompressionService
            
            logger.info(f"Compressing GIF to stay under {args.max_size_mb:.2f} MB...")
            compression_service = CompressionService()
            
            compression_result = compression_service.compress_gif_file(
                input_path=gif_path,
                target_filename=args.rename_output,
                max_size_mb=args.max_size_mb
            )
            
            if compression_result.get('success'):
                logger.info(f"✅ GIF compressed successfully!")
                logger.info(f"Size reduction: {compression_result['compression_ratio']:.1f}%")
                logger.info(f"Final size: {compression_result['final_size_mb']:.2f} MB")
                gif_path = compression_result['output_file']
            else:
                logger.warning(f"⚠️ Compression failed: {compression_result.get('error', 'Unknown error')}")
                logger.warning("Continuing with uncompressed GIF...")
        
        print(f"SUCCESS: GIF created at {gif_path}")
        
    except Exception as e:
        logger.error(f"Failed to create GIF: {e}")
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
