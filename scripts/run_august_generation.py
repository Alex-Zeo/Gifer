#!/usr/bin/env python3
"""
Python alternative to PowerShell script for generating August 2025 GIFs.
This provides a cross-platform solution.
"""

import asyncio
import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# Add app to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from app.logger import get_logger

logger = get_logger(__name__)


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {description}")
        logger.error(f"Exit code: {e.returncode}")
        if e.stdout:
            logger.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Stderr: {e.stderr}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Generate GIFs for August 2025")
    parser.add_argument("--overwrite-screenshots", action="store_true", help="Overwrite existing screenshots")
    parser.add_argument("--upload-to-drive", action="store_true", help="Upload GIFs to Google Drive")
    parser.add_argument("--drive-folder-id", help="Google Drive folder ID")
    parser.add_argument("--make-public", action="store_true", help="Make Google Drive files public")
    parser.add_argument("--seconds-per-image", type=float, default=0.5, help="Seconds per image in GIF")
    
    args = parser.parse_args()
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent.parent
    if not (project_root / "scripts" / "scrape_screenshots.py").exists():
        logger.error("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Create output directories
    converter_dir = project_root / "converter" / "images"
    results_dir = project_root / "results" / "gifs"
    converter_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Output directories created.")
    
    # Step 1: Scrape screenshots for August 2025
    logger.info("Step 1: Scraping screenshots for August 2025...")
    
    screenshot_cmd = [
        sys.executable,
        str(project_root / "scripts" / "scrape_screenshots.py"),
        "--start-date", "2025-08-01",
        "--end-date", "2025-08-31",
        "--output-dir", str(converter_dir)
    ]
    
    if args.overwrite_screenshots:
        screenshot_cmd.append("--overwrite")
    
    if not run_command(screenshot_cmd, "Scraping screenshots"):
        logger.error("Screenshot scraping failed")
        sys.exit(1)
    
    logger.info("Screenshots completed successfully!")
    
    # Step 2: Generate GIFs for each day
    logger.info("Step 2: Generating GIFs for each day...")
    
    # Find all directories that match the pattern gpsjam-2025-08-*
    date_dirs = sorted([d for d in converter_dir.iterdir() 
                       if d.is_dir() and d.name.startswith("gpsjam-2025-08-")])
    
    if not date_dirs:
        logger.error(f"No screenshot directories found in {converter_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(date_dirs)} directories to process.")
    
    success_count = 0
    error_count = 0
    
    for date_dir in date_dirs:
        output_path = results_dir / f"{date_dir.name}.gif"
        
        logger.info(f"Processing {date_dir.name}...")
        
        gif_cmd = [
            sys.executable,
            str(project_root / "scripts" / "make_gif.py"),
            "--input-dir", str(date_dir),
            "--output-path", str(output_path),
            "--seconds-per-image", str(args.seconds_per_image)
        ]
        
        if args.upload_to_drive:
            gif_cmd.append("--upload-to-drive")
            if args.drive_folder_id:
                gif_cmd.extend(["--drive-folder-id", args.drive_folder_id])
            if args.make_public:
                gif_cmd.append("--make-public")
        
        if run_command(gif_cmd, f"Creating GIF for {date_dir.name}"):
            success_count += 1
            logger.info(f"✓ Successfully created GIF for {date_dir.name}")
        else:
            error_count += 1
            logger.error(f"✗ Failed to create GIF for {date_dir.name}")
    
    # Summary
    logger.info("=== SUMMARY ===")
    logger.info(f"Total directories processed: {len(date_dirs)}")
    logger.info(f"Successful GIFs created: {success_count}")
    logger.info(f"Failed GIFs: {error_count}")
    
    if error_count == 0:
        logger.info("All GIFs generated successfully! 🎉")
        logger.info(f"GIFs are located in: {results_dir}")
    else:
        logger.warning("Some GIFs failed to generate. Check the logs above for details.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
