#!/usr/bin/env python3
"""
Script to scrape screenshots from gpsjam.org for specific dates.
"""

import asyncio
import argparse
from datetime import date
from pathlib import Path
import sys

# Add app to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))

from app.services.screenshot_service import ScreenshotAgent
from app.logger import get_logger
from app.config import settings

logger = get_logger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Scrape screenshots from gpsjam.org")
    parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default=settings.CONVERTER_DIR, help="Output directory")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing screenshots")
    parser.add_argument("--lat", type=float, default=57.48042, help="Latitude")
    parser.add_argument("--lon", type=float, default=21.30953, help="Longitude")
    parser.add_argument("--zoom", type=float, default=5.0, help="Zoom level")
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = date.fromisoformat(args.start_date)
    end_date = date.fromisoformat(args.end_date)
    
    # Generate base URL (without date parameter)
    base_url = f"https://gpsjam.org/?lat={args.lat}&lon={args.lon}&z={args.zoom}"
    
    # Create output directory
    output_dir = Path(args.output_dir) / "gpsjam-2025-08"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Processing dates from {start_date} to {end_date}")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Output directory: {output_dir}")
    
    # Create ScreenshotAgent and capture date range
    agent = ScreenshotAgent(
        headless=settings.PLAYWRIGHT_HEADLESS,
        timeout_ms=settings.PLAYWRIGHT_TIMEOUT_MS,
        concurrency=settings.CONCURRENCY_MAX,
        rps=settings.PER_HOST_RPS,
    )
    
    # Enhanced render wait configuration for reliable map screenshots
    render_wait_config = {
        "wait_until": ["domcontentloaded", "networkidle"],
        "ensure_images_loaded": True,
        "ensure_fonts_loaded": True,
        "extra_wait_ms": 1000,  # Extra wait for map animations
        "timeout_ms": settings.PLAYWRIGHT_TIMEOUT_MS
    }
    
    try:
        screenshots = await agent.capture_date_range(
            url=base_url,
            start_date=start_date,
            end_date=end_date,
            out_dir=str(output_dir),
            date_param_name="date",
            date_format="YYYY-MM-DD",
            timezone="UTC",
            viewport={"width": 1920, "height": 1080},
            full_page=True,
            render_wait=render_wait_config,
            overwrite=args.overwrite,
        )
        
        logger.info(f"Successfully captured {len(screenshots)} screenshots")
        for screenshot in screenshots:
            logger.info(f"Screenshot: {screenshot}")
            
    except Exception as e:
        logger.error(f"Failed to capture screenshots: {e}")
        sys.exit(1)
    
    logger.info("Screenshot scraping completed!")


if __name__ == "__main__":
    asyncio.run(main())
